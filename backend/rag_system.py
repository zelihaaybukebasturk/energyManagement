"""
Retrieval-Augmented Generation (RAG) System
Provides AI-powered explanations and recommendations based on
energy efficiency analysis results and technical knowledge base.
"""

import os
from typing import Dict, List, Optional
from pathlib import Path
import json

try:
    from llm_client import get_llm_client, LLMClient, TemplateLLMClient
except ImportError:
    # Fallback if llm_client not available
    from llm_client import get_llm_client, LLMClient
    TemplateLLMClient = None


class RAGSystem:
    """RAG system for generating AI explanations and recommendations."""
    
    def __init__(self, knowledge_base_path: Optional[str] = None, llm_client: Optional[LLMClient] = None):
        """
        Initialize the RAG system.
        
        Args:
            knowledge_base_path: Path to knowledge base directory (defaults to ../knowledge_base from backend/)
            llm_client: LLM client instance (defaults to auto-detected client)
        """
        if knowledge_base_path is None:
            # Default: assume running from backend/, knowledge_base is one level up
            script_dir = Path(__file__).parent
            self.knowledge_base_path = script_dir.parent / "knowledge_base"
        else:
            self.knowledge_base_path = Path(knowledge_base_path)
        
        self.knowledge_base_path.mkdir(exist_ok=True, parents=True)
        self.documents = []
        self.llm_client = llm_client or get_llm_client()
        # Check if using template client (fallback)
        if TemplateLLMClient:
            self.use_llm = not isinstance(self.llm_client, TemplateLLMClient)
        else:
            # Check by class name if import failed
            self.use_llm = "Template" not in type(self.llm_client).__name__
        self._load_knowledge_base()
    
    def _load_knowledge_base(self):
        """Load documents from the knowledge base."""
        # Load structured knowledge documents
        knowledge_files = [
            "energy_standards.json",
            "hvac_best_practices.json",
            "lighting_guidelines.json",
            "retrofit_strategies.json",
            "whatif_playbook.json",
        ]
        
        for filename in knowledge_files:
            filepath = self.knowledge_base_path / filename
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.documents.append({
                        "source": filename,
                        "content": data
                    })
    
    def retrieve_relevant_documents(
        self,
        building_type: str,
        efficiency_level: str,
        energy_per_sqm: float
    ) -> List[Dict]:
        """
        Retrieve relevant documents based on analysis results.
        
        Args:
            building_type: Type of building
            efficiency_level: Efficiency classification
            energy_per_sqm: Energy consumption per square meter
        
        Returns:
            List of relevant document snippets
        """
        relevant_docs = []
        
        # Always include general energy standards
        for doc in self.documents:
            if doc["source"] == "energy_standards.json":
                relevant_docs.append(doc)
        
        # Include building-type specific documents
        for doc in self.documents:
            content = doc["content"]
            
            # Include HVAC practices for inefficient buildings
            if efficiency_level == "inefficient" and doc["source"] == "hvac_best_practices.json":
                relevant_docs.append(doc)
            
            # Include lighting guidelines for moderate/inefficient
            if efficiency_level in ["moderately_efficient", "inefficient"] and doc["source"] == "lighting_guidelines.json":
                relevant_docs.append(doc)
            
            # Include retrofit strategies for inefficient buildings
            if efficiency_level == "inefficient" and doc["source"] == "retrofit_strategies.json":
                relevant_docs.append(doc)
        
        return relevant_docs

    def retrieve_relevant_documents_for_whatif(self, scenario: str) -> List[Dict]:
        """
        Retrieve relevant knowledge-base documents for a selected what-if scenario.
        """
        scenario = (scenario or "").strip().lower()
        sources = {"energy_standards.json", "whatif_playbook.json"}
        if scenario == "led":
            sources |= {"lighting_guidelines.json", "retrofit_strategies.json"}
        elif scenario == "occupancy_down_20":
            sources |= {"hvac_best_practices.json", "energy_standards.json"}
        elif scenario == "hours_shorter":
            sources |= {"hvac_best_practices.json", "lighting_guidelines.json"}
        else:
            sources |= {"lighting_guidelines.json", "hvac_best_practices.json"}

        out = []
        for doc in self.documents:
            if doc.get("source") in sources:
                out.append(doc)
        return out

    def generate_whatif_explanation(
        self,
        scenario: str,
        simulation_result: Dict,
        relevant_docs: List[Dict],
        weather_payload: Optional[Dict] = None,
    ) -> Dict[str, str]:
        """
        Generate AI explanation for what-if simulation (RAG + optional LLM).

        Output is always Turkish when possible:
        - Main model: analysis + scenario generation (English preferred for stability)
        - Second model: translation to Turkish (LLM-based translator)
        """
        scenario = (scenario or "").strip().lower()

        # Compact doc context to avoid huge prompts
        doc_context = []
        for doc in relevant_docs:
            try:
                doc_context.append(f"SOURCE: {doc['source']}\n{json.dumps(doc['content'], ensure_ascii=False)[:2500]}")
            except Exception:
                continue
        docs_blob = "\n\n".join(doc_context)

        system_prompt = (
            "You are an expert building energy analyst.\n"
            "Your task: interpret a what-if energy/KPI simulation, cite practical guidance from provided documents, "
            "and propose 3 actionable solution options.\n"
            "Write in clear, structured Markdown with headings and bullet points.\n"
        )

        # English prompt (then translate with a *second* model call)
        prompt = f"""
WHAT-IF SCENARIO: {scenario}

SIMULATION_RESULT_JSON:
{json.dumps(simulation_result, indent=2)}

WEATHER_CONTEXT_JSON (optional):
{json.dumps(weather_payload, indent=2) if weather_payload else "null"}

KNOWLEDGE_BASE_EXCERPTS (RAG):
{docs_blob}

Write your response in ENGLISH (it will be translated to Turkish by a second model call).

Please produce:
1) One short executive summary sentence (factual) like:
   "These changes improve energy efficiency by X% and the estimated annual savings are Y TL."
2) A contextual interpretation referencing the RAG excerpts.
3) Three solution scenarios in the format:
   - Scenario 1: If you choose ... then ...
   - Scenario 2: If you choose ... then ...
   - Scenario 3: If you choose ... then ...

Return Markdown with sections:
## Summary
## Interpretation (with RAG)
## 3 Solution Scenarios
""".strip()

        llm_used = False
        raw = ""
        try:
            raw = self.llm_client.generate(prompt, system_prompt)
            llm_used = self.use_llm
        except Exception as e:
            # Template fallback (Turkish directly)
            delta = (simulation_result.get("delta") or {})
            pct = delta.get("savings_percent")
            tl = delta.get("annual_savings_tl_est")
            raw = (
                "## Özet\n"
                f"Bu değişiklikler enerji tüketimini yaklaşık %{pct} azaltır ve yıllık tahmini tasarruf {tl} TL olur.\n\n"
                "## Yorum (RAG ile)\n"
                "- Bu çıktı, bilgi tabanındaki genel aydınlatma/HVAC en iyi uygulamaları ve what-if oyun kitabındaki tipik etki aralıkları ile uyumludur.\n"
                "- Gerçek tasarruf; kullanım profili, ekipman verimliliği ve planlama disiplinine göre değişir.\n\n"
                "## 3 Çözüm Senaryosu\n"
                "- Senaryo 1: Seçersen temel önlemi uygularsın; sonucu orta düzey tasarruf.\n"
                "- Senaryo 2: Seçersen kontrol/otomasyon eklersin; sonucu daha yüksek tasarruf.\n"
                "- Senaryo 3: Seçersen kapsamı genişletirsin; sonucu en yüksek tasarruf.\n"
            )

        # Translation step (second model) — preferred
        tr_text = raw
        translation_used = False
        try:
            from translation_client import translate_to_turkish_llm
            tr_text = translate_to_turkish_llm(raw)
            translation_used = True
        except Exception as tr_err:
            # Fallback to deep-translator (legacy)
            try:
                tr_text = self._translate_to_turkish(raw)
            except Exception:
                tr_text = raw

        return {
            "text": tr_text,
            "sources_used": [doc.get("source") for doc in relevant_docs],
            "llm_used": bool(llm_used),
            "translation_used": bool(translation_used),
        }
    
    def generate_explanation(
        self,
        kpis: Dict,
        efficiency_result: Dict,
        relevant_docs: List[Dict],
        dataset_context: Optional[str] = None,
        weather_payload: Optional[Dict] = None,
    ) -> Dict[str, str]:
        """
        Generate AI explanation based on KPIs, efficiency results, and retrieved documents.
        dataset_context: optional text from auxiliary Excel dataset (similar buildings) for RAG.
        """
        building_type = efficiency_result["building_type"]
        efficiency_level = efficiency_result["efficiency_level"]
        energy_per_sqm = efficiency_result["annual_energy_per_sqm"]
        benchmarks = efficiency_result["benchmarks"]
        
        # Extract key information from documents
        standards_info = ""
        hvac_info = ""
        lighting_info = ""
        retrofit_info = ""
        
        for doc in relevant_docs:
            if doc["source"] == "energy_standards.json":
                standards_info = json.dumps(doc["content"], indent=2)
            elif doc["source"] == "hvac_best_practices.json":
                hvac_info = json.dumps(doc["content"], indent=2)
            elif doc["source"] == "lighting_guidelines.json":
                lighting_info = json.dumps(doc["content"], indent=2)
            elif doc["source"] == "retrofit_strategies.json":
                retrofit_info = json.dumps(doc["content"], indent=2)
        
        # Try to use LLM for generation, fallback to templates if not available
        try:
            # Build prompt for LLM (optionally include auxiliary dataset context)
            prompt = self._build_llm_prompt(
                building_type,
                efficiency_level,
                energy_per_sqm,
                benchmarks,
                kpis,
                standards_info,
                hvac_info,
                lighting_info,
                retrofit_info,
                dataset_context=dataset_context,
                weather_payload=weather_payload,
            )
            
            system_prompt = """You are an expert energy efficiency consultant specializing in building energy performance analysis. 
Your role is to analyze building energy data, explain efficiency classifications, and provide actionable recommendations 
based on industry standards and best practices. Be clear, professional, and data-driven in your explanations.
Use "Explanation" and "Recommendations" as section headers."""
            
            # Generate using LLM (in English)
            llm_response = self.llm_client.generate(prompt, system_prompt)
            
            # Parse LLM response
            explanation, recommendations = self._parse_llm_response(llm_response, building_type, efficiency_level, energy_per_sqm, benchmarks, kpis)
            
        except Exception as e:
            # Fallback to template-based if LLM fails
            print(f"LLM generation failed, using templates: {e}")
            explanation = self._build_explanation(
                building_type,
                efficiency_level,
                energy_per_sqm,
                benchmarks,
                kpis,
                standards_info,
                hvac_info,
                lighting_info,
                retrofit_info
            )
            
            recommendations = self._build_recommendations(
                efficiency_level,
                building_type,
                energy_per_sqm,
                benchmarks,
                hvac_info,
                lighting_info,
                retrofit_info
            )
        
        # Always translate to Turkish (for both LLM and template output)
        try:
            # Prefer LLM-based translation (2nd model) when available
            try:
                from translation_client import translate_to_turkish_llm
                explanation = translate_to_turkish_llm(explanation)
                recommendations = translate_to_turkish_llm(recommendations)
            except Exception:
                explanation = self._translate_to_turkish(explanation)
                recommendations = self._translate_to_turkish(recommendations)
        except Exception as tr_err:
            print(f"Translation failed, keeping original: {tr_err}")
        
        return {
            "explanation": explanation,
            "recommendations": recommendations,
            "sources_used": [doc["source"] for doc in relevant_docs],
            "llm_used": self.use_llm
        }
    
    def _build_explanation(
        self,
        building_type: str,
        efficiency_level: str,
        energy_per_sqm: float,
        benchmarks: Dict,
        kpis: Dict,
        standards_info: str,
        hvac_info: str,
        lighting_info: str,
        retrofit_info: str
    ) -> str:
        """Build the explanation text."""
        
        efficiency_descriptions = {
            "efficient": "excellent",
            "moderately_efficient": "moderate",
            "inefficient": "poor"
        }
        
        desc = efficiency_descriptions.get(efficiency_level, "moderate")
        
        explanation = f"""
## Energy Efficiency Analysis for {building_type.capitalize()} Building

**Current Performance:**
Your building consumes {energy_per_sqm:.1f} kWh/m²/year, which is classified as **{desc}** efficiency.

**Benchmark Comparison:**
- Excellent performance threshold: {benchmarks['efficient']} kWh/m²/year
- Average performance threshold: {benchmarks['moderate']} kWh/m²/year
- Poor performance threshold: {benchmarks['inefficient']} kWh/m²/year

**Key Metrics:**
- Total Energy Consumption: {kpis.get('total_energy_kwh', 0):.1f} kWh
- Building Area: {kpis.get('building_area_m2', 0):.1f} m²
"""
        
        if kpis.get('energy_per_occupant_kwh'):
            explanation += f"- Energy per Occupant: {kpis['energy_per_occupant_kwh']:.1f} kWh\n"
        
        if efficiency_level == "inefficient":
            explanation += f"""
**Efficiency Assessment:**
Your building's energy consumption exceeds the moderate threshold by {energy_per_sqm - benchmarks['moderate']:.1f} kWh/m²/year. 
This indicates significant opportunities for energy efficiency improvements.

**Likely Contributing Factors:**
Based on energy efficiency standards and best practices, common causes of high energy consumption in {building_type} buildings include:
- Inefficient HVAC systems or improper scheduling
- Poor building envelope insulation
- Outdated lighting systems
- Inadequate energy management practices
"""
        elif efficiency_level == "moderately_efficient":
            explanation += f"""
**Efficiency Assessment:**
Your building performs at an average level. While meeting basic standards, there is room for improvement 
to reach excellent efficiency levels.

**Potential Improvements:**
Consider implementing targeted efficiency measures to reduce consumption from {energy_per_sqm:.1f} kWh/m²/year 
to below {benchmarks['efficient']} kWh/m²/year.
"""
        else:
            explanation += """
**Efficiency Assessment:**
Your building demonstrates excellent energy efficiency performance. Continue monitoring and maintaining 
current systems to sustain this level of performance.
"""
        
        return explanation.strip()
    
    def _build_recommendations(
        self,
        efficiency_level: str,
        building_type: str,
        energy_per_sqm: float,
        benchmarks: Dict,
        hvac_info: str,
        lighting_info: str,
        retrofit_info: str
    ) -> str:
        """Build recommendations text."""
        
        recommendations = "## Recommended Actions\n\n"
        
        if efficiency_level == "inefficient":
            recommendations += """
**Priority 1: Immediate Actions (High Impact)**
1. **HVAC System Optimization**
   - Conduct an energy audit of HVAC systems
   - Optimize ventilation schedules based on occupancy patterns
   - Install programmable thermostats and zone controls
   - Consider upgrading to high-efficiency HVAC equipment

2. **Building Envelope Improvements**
   - Assess and improve insulation in walls, roof, and windows
   - Seal air leaks and improve weatherization
   - Upgrade windows to energy-efficient models if needed

3. **Lighting System Upgrade**
   - Replace inefficient lighting with LED technology
   - Implement occupancy sensors and daylight harvesting
   - Optimize lighting schedules

**Priority 2: Medium-Term Improvements**
4. **Energy Management Systems**
   - Install building energy management system (BEMS)
   - Implement sub-metering for better monitoring
   - Establish energy performance tracking and reporting

5. **Operational Improvements**
   - Train staff on energy-efficient practices
   - Regular maintenance of HVAC and lighting systems
   - Optimize equipment schedules based on actual usage

**Priority 3: Long-Term Investments**
6. **Renewable Energy Integration**
   - Consider solar PV installation
   - Evaluate on-site renewable energy opportunities

**Expected Impact:**
Implementing Priority 1 actions could reduce energy consumption by 20-30%, bringing your building 
closer to moderate efficiency levels. Full implementation of all recommendations could achieve 
excellent efficiency performance.
"""
        elif efficiency_level == "moderately_efficient":
            recommendations += """
**Recommended Actions to Achieve Excellent Efficiency:**

1. **Targeted Efficiency Measures**
   - Focus on HVAC optimization and scheduling
   - Upgrade lighting systems to LED with smart controls
   - Improve building envelope where cost-effective

2. **Energy Monitoring**
   - Implement detailed energy monitoring and sub-metering
   - Track performance trends and identify anomalies

3. **Operational Excellence**
   - Fine-tune operational schedules
   - Regular maintenance and optimization

**Expected Impact:**
These measures can help reduce energy consumption to excellent efficiency levels 
(below {:.1f} kWh/m²/year).
""".format(benchmarks['efficient'])
        else:
            recommendations += """
**Maintenance Recommendations:**

1. **Sustain Performance**
   - Continue regular maintenance of all systems
   - Monitor energy consumption trends
   - Stay updated with latest efficiency technologies

2. **Continuous Improvement**
   - Consider periodic energy audits
   - Explore advanced efficiency technologies
   - Maintain operational best practices

Your building is already performing excellently. Focus on maintaining this performance level.
"""
        
        return recommendations.strip()
    
    def _build_llm_prompt(
        self,
        building_type: str,
        efficiency_level: str,
        energy_per_sqm: float,
        benchmarks: Dict,
        kpis: Dict,
        standards_info: str,
        hvac_info: str,
        lighting_info: str,
        retrofit_info: str,
        dataset_context: Optional[str] = None,
        weather_payload: Optional[Dict] = None,
    ) -> str:
        """Build prompt for LLM generation."""
        
        efficiency_descriptions = {
            "efficient": "excellent",
            "moderately_efficient": "moderate",
            "inefficient": "poor"
        }
        desc = efficiency_descriptions.get(efficiency_level, "moderate")
        
        prompt = f"""Analyze the following building energy efficiency data and provide a comprehensive explanation and recommendations.

BUILDING INFORMATION:
- Building Type: {building_type.capitalize()}
- Total Energy Consumption: {kpis.get('total_energy_kwh', 0):.1f} kWh
- Building Area: {kpis.get('building_area_m2', 0):.1f} m²
"""
        
        if kpis.get('energy_per_occupant_kwh'):
            prompt += f"- Occupancy: {kpis.get('occupancy', 'N/A')} occupants\n"
            prompt += f"- Energy per Occupant: {kpis['energy_per_occupant_kwh']:.1f} kWh\n"
        
        prompt += f"""
ENERGY PERFORMANCE:
- Annual Energy per m²: {energy_per_sqm:.1f} kWh/m²/year
- Efficiency Classification: {desc.upper()} ({efficiency_level})
- Energy per m² (for selected period): {kpis.get('energy_per_sqm_kwh', 0):.2f} kWh/m²

BENCHMARKS:
- Excellent threshold: {benchmarks['efficient']} kWh/m²/year
- Moderate threshold: {benchmarks['moderate']} kWh/m²/year
- Inefficient threshold: {benchmarks['inefficient']} kWh/m²/year
"""
        if weather_payload:
            try:
                wx = json.dumps(weather_payload, ensure_ascii=False, indent=2)
            except Exception:
                wx = str(weather_payload)
            prompt += f"""
WEATHER / LOCATION CONTEXT (optional):
{wx}
"""
        if dataset_context:
            prompt += f"""
AUXILIARY DATASET (similar buildings / reference data):
{dataset_context}
"""
        prompt += f"""
RELEVANT TECHNICAL DOCUMENTS:
{standards_info}
{hvac_info if hvac_info else ''}
{lighting_info if lighting_info else ''}
{retrofit_info if retrofit_info else ''}

Please provide:
1. A detailed explanation of the building's energy efficiency performance
2. Analysis of why it is classified as {desc} efficiency
3. Specific, actionable recommendations based on the technical documents provided
4. Expected impact of recommended actions

Format your response with clear sections: "## Explanation" and "## Recommendations"."""
        
        return prompt
    
    def _parse_llm_response(
        self,
        llm_response: str,
        building_type: str,
        efficiency_level: str,
        energy_per_sqm: float,
        benchmarks: Dict,
        kpis: Dict
    ) -> tuple:
        """Parse LLM response into explanation and recommendations."""
        
        # Try to split by section markers (Turkish or English)
        explanation = ""
        recommendations = ""
        for sep in ["## Öneriler", "**Öneriler**", "## Recommendations", "**Recommendations**", "Öneriler", "Recommendations"]:
            if sep in llm_response:
                parts = llm_response.split(sep, 1)
                explanation = parts[0].replace("## Açıklama", "").replace("**Açıklama**", "").replace("## Explanation", "").replace("**Explanation**", "").strip()
                recommendations = parts[1].strip() if len(parts) > 1 else "Yukarıdaki açıklamaya bakınız."
                break
        else:
            # If no clear split, use first 60% as explanation, rest as recommendations
            split_point = int(len(llm_response) * 0.6)
            explanation = llm_response[:split_point].replace("## Açıklama", "").replace("**Açıklama**", "").replace("## Explanation", "").replace("**Explanation**", "").strip()
            recommendations = llm_response[split_point:].strip()
        
        # Add header if missing (English - will be translated to Turkish later)
        if explanation and not explanation.startswith("#"):
            explanation = f"## Energy Efficiency Analysis for {building_type.capitalize()} Building\n\n{explanation}"
        
        if recommendations and not recommendations.startswith("#"):
            recommendations = f"## Recommended Actions\n\n{recommendations}"
        
        return explanation, recommendations
    
    def _translate_to_turkish(self, text: str) -> str:
        """Translate English text to Turkish using Google Translate (deep-translator) as fallback."""
        if not text or len(text.strip()) < 5:
            return text
        try:
            from deep_translator import GoogleTranslator
        except ImportError:
            print("deep-translator not installed. Run: pip install deep-translator")
            return text
        
        # Google Translate has ~5000 char limit per request; chunk by paragraphs
        max_chunk = 4500
        translator = GoogleTranslator(source='en', target='tr')
        if len(text) <= max_chunk:
            result = translator.translate(text)
            return result if result else text
        
        chunks = []
        current = []
        current_len = 0
        for para in text.split('\n\n'):
            para_len = len(para) + 2
            if current_len + para_len > max_chunk and current:
                chunks.append('\n\n'.join(current))
                current = [para]
                current_len = para_len
            else:
                current.append(para)
                current_len += para_len
        if current:
            chunks.append('\n\n'.join(current))
        
        return '\n\n'.join(translator.translate(c) or c for c in chunks)

