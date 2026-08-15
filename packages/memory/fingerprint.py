from typing import List
from packages.contracts.domain import Incident, Symptom, Evidence, IncidentFingerprint

class IncidentFingerprinter:
    def fingerprint(self, incident: Incident, symptoms: List[Symptom], evidence: List[Evidence]) -> IncidentFingerprint:
        services = set()
        metrics = set()
        
        for symptom in symptoms:
            if hasattr(symptom, 'service'):
                services.add(symptom.service)
                
        for ev in evidence:
            if hasattr(ev, 'metric_name'):
                metrics.add(ev.metric_name)
            if hasattr(ev, 'service'):
                services.add(ev.service)

        # In a real system, we'd also generate embeddings here using EmbeddingProvider
        return IncidentFingerprint(
            services=list(services),
            metric_patterns=list(metrics),
            symptoms=[s.description for s in symptoms]
        )

    def similarity(self, a: IncidentFingerprint, b: IncidentFingerprint) -> float:
        # Structural similarity (0-1) based on shared symptoms, services, metric patterns
        def jaccard(set1, set2):
            if not set1 and not set2:
                return 1.0
            return len(set1.intersection(set2)) / len(set1.union(set2)) if set1 or set2 else 0.0

        services_sim = jaccard(set(a.services), set(b.services))
        metrics_sim = jaccard(set(a.metric_patterns), set(b.metric_patterns))
        
        # Simple weighted average
        return (services_sim * 0.6) + (metrics_sim * 0.4)

    def to_text(self, fp: IncidentFingerprint) -> str:
        services_text = ", ".join(fp.services)
        metrics_text = ", ".join(fp.metric_patterns)
        symptoms_text = ". ".join(fp.symptoms)
        
        return f"Services: {services_text}\nMetrics: {metrics_text}\nSymptoms: {symptoms_text}"
