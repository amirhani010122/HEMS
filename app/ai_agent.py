import httpx
from app.config import settings
from app.models import AIResponse, Consumption
from typing import List
import logging

logger = logging.getLogger(__name__)

class AIAgent:
    def __init__(self):
        self.base_url = settings.AI_AGENT_URL

    async def analyze_consumption(self, consumptions: List[Consumption], current_data: dict) -> AIResponse:
        """
        Send consumption data to AI Agent for analysis and prediction
        """
        try:
            # Prepare data for AI analysis
            analysis_data = {
                "historical_consumptions": [
                    {
                        "timestamp": cons.timestamp.isoformat(),
                        "power_usage_kwh": cons.power_usage_kwh,
                        "devices_on": cons.devices_on,
                        "temperature": cons.temperature_c
                    }
                    for cons in consumptions[-24:]  # Last 24 readings
                ],
                "current_conditions": current_data
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(f"{self.base_url}", json=analysis_data)
                response.raise_for_status()
                
                ai_result = response.json()
                
                return AIResponse(
                    predicted_consumption_kwh=ai_result.get("predicted_consumption_kwh", 0),
                    suggestion=ai_result.get("suggestion", "No suggestion available"),
                    risk_level=ai_result.get("risk_level", "Medium"),
                    model_version=ai_result.get("model_version", "v1.0")
                )
                
        except Exception as e:
            logger.error(f"AI Agent error: {e}")
            # Return default response if AI service is unavailable
            return AIResponse(
                predicted_consumption_kwh=current_data.get("power_usage_kwh", 0) * 1.1,
                suggestion="Continue normal usage patterns",
                risk_level="Medium",
                model_version="v1.0-fallback"
            )

ai_agent = AIAgent()