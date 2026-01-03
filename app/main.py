# app/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
import time

from app.models import PromptRequest, RouterResponse, StatsResponse
from app.database import get_db, RequestLog, ModelStats, init_db
from app.router.classifier import PromptClassifier
from app.router.model_clients import ModelRouter
from app.config import settings, MODEL_COSTS, DIFFICULTY_TO_MODEL

# Initialize FastAPI app
app = FastAPI(
    title="Smart Model Router API",
    description="Cost-optimized AI routing system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
classifier = PromptClassifier()
router = ModelRouter()

@app.on_event("startup")
def startup_event():
    """Initialize database on startup"""
    init_db()
    print("🚀 Smart Model Router API is running!")
    print(f"📊 Simple: {settings.simple_model} | Medium: {settings.medium_model} | Complex: {settings.complex_model}")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Smart Model Router",
        "version": "1.0.0"
    }

@app.post("/generate", response_model=RouterResponse)
async def generate(
    request: PromptRequest,
    db: Session = Depends(get_db)
):
    """
    Main endpoint: Classifies prompt and routes to appropriate model
    """
    start_time = time.time()
    
    try:
        # Step 1: Classify the prompt
        classification = classifier.classify(request.prompt)
        
        # Step 2: Route to appropriate model
        response_data, model_used = await router.route_and_generate(
            difficulty=classification.difficulty,
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        # Check if generation was successful
        if response_data["status"] == "error":
            raise HTTPException(status_code=500, detail=response_data["response"])
        
        # Step 3: Calculate costs
        total_latency = (time.time() - start_time) * 1000
        tokens_used = response_data["tokens_used"]
        
        # Cost of chosen model
        cost_per_token = MODEL_COSTS[model_used]
        actual_cost = tokens_used * cost_per_token
        
        # Cost if we always used GPT-4o
        gpt4o_cost = tokens_used * MODEL_COSTS["gpt-4o"]
        cost_saved = gpt4o_cost - actual_cost
        
        # Step 4: Log to database
        log_entry = RequestLog(
            prompt=request.prompt,
            prompt_tokens=tokens_used,
            difficulty=classification.difficulty,
            confidence=classification.confidence,
            selected_model=model_used,
            response=response_data["response"],
            response_tokens=tokens_used,
            latency_ms=total_latency,
            cost_usd=actual_cost,
            cost_saved_usd=cost_saved,
            user_id=request.user_id,
            status="success"
        )
        db.add(log_entry)
        
        # Update model stats
        model_stat = db.query(ModelStats).filter(ModelStats.model_name == model_used).first()
        if model_stat:
            model_stat.total_requests += 1
            model_stat.total_tokens += tokens_used
            model_stat.total_cost_usd += actual_cost
            model_stat.avg_latency_ms = (
                (model_stat.avg_latency_ms * (model_stat.total_requests - 1) + total_latency) 
                / model_stat.total_requests
            )
        else:
            model_stat = ModelStats(
                model_name=model_used,
                total_requests=1,
                total_tokens=tokens_used,
                total_cost_usd=actual_cost,
                avg_latency_ms=total_latency
            )
            db.add(model_stat)
        
        db.commit()
        db.refresh(log_entry)
        
        # Step 5: Return response
        return RouterResponse(
            response=response_data["response"],
            model_used=model_used,
            difficulty=classification.difficulty,
            classification_confidence=classification.confidence,
            tokens_used=tokens_used,
            cost_usd=round(actual_cost, 6),
            cost_saved_usd=round(cost_saved, 6),
            latency_ms=round(total_latency, 2),
            request_id=log_entry.id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Log error
        error_log = RequestLog(
            prompt=request.prompt,
            difficulty="unknown",
            confidence=0.0,
            selected_model="error",
            response=f"Error: {str(e)}",
            user_id=request.user_id,
            status="error"
        )
        db.add(error_log)
        db.commit()
        
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.get("/stats", response_model=StatsResponse)
async def get_stats(db: Session = Depends(get_db)):
    """Get system statistics and cost savings"""
    
    logs = db.query(RequestLog).filter(RequestLog.status == "success").all()
    model_stats = db.query(ModelStats).all()
    
    if not logs:
        return StatsResponse(
            total_requests=0,
            total_cost_usd=0.0,
            total_saved_usd=0.0,
            model_breakdown={},
            avg_latency_ms=0.0
        )
    
    total_cost = sum(log.cost_usd for log in logs)
    total_saved = sum(log.cost_saved_usd for log in logs)
    avg_latency = sum(log.latency_ms for log in logs) / len(logs)
    
    model_breakdown = {}
    for stat in model_stats:
        model_breakdown[stat.model_name] = {
            "requests": stat.total_requests,
            "total_tokens": stat.total_tokens,
            "total_cost_usd": round(stat.total_cost_usd, 4),
            "avg_latency_ms": round(stat.avg_latency_ms, 2)
        }
    
    return StatsResponse(
        total_requests=len(logs),
        total_cost_usd=round(total_cost, 4),
        total_saved_usd=round(total_saved, 4),
        model_breakdown=model_breakdown,
        avg_latency_ms=round(avg_latency, 2)
    )

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "models": {
            "simple": settings.simple_model,
            "medium": settings.medium_model,
            "complex": settings.complex_model
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)