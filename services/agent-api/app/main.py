"""komatsuna-ai-agent API エントリポイント."""

from fastapi import FastAPI

from app.routers import daily_summary, export_research_data, health, improve, judge, watering_effect

app = FastAPI(
    title="komatsuna-ai-agent API",
    description="小松菜栽培 AI 判断・効果分析 API",
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(judge.router)
app.include_router(watering_effect.router)
app.include_router(improve.router)
app.include_router(daily_summary.router)
app.include_router(export_research_data.router)
