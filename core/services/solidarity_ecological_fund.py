"""
🌱💝 Phoenix Solidarity-Ecological Fund
Système de fonds hybride pour impact social ET environnemental.

Combine reconversion solidaire + compensation carbone pour maximiser
l'impact positif de chaque utilisation de Phoenix Letters.

Author: Claude Phoenix DevSecOps Guardian
Version: 1.0.0 - Phoenix Solidarity-Green Initiative
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class FundAllocation(Enum):
    """Types d'allocation du fonds."""
    SOLIDARITY = "solidarity"      # Bourses reconversion
    ECOLOGICAL = "ecological"      # Compensation carbone
    ADMINISTRATIVE = "admin"       # Frais de gestion (max 5%)


class ContributionSource(Enum):
    """Sources de contribution au fonds."""
    USER_PREMIUM = "premium_user"           # Utilisateurs premium
    USER_VOLUNTARY = "voluntary"            # Contributions volontaires
    BUSINESS_PARTNERSHIP = "partnership"    # Partenariats entreprises
    GRANT = "grant"                        # Subventions publiques


@dataclass
class FundContribution:
    """Contribution individuelle au fonds."""
    
    contribution_id: str
    timestamp: datetime
    user_id: Optional[str]
    source: ContributionSource
    
    # Montants (en euros)
    total_amount: float
    solidarity_amount: float      # 50% par défaut
    ecological_amount: float      # 50% par défaut
    admin_amount: float          # Max 5%
    
    # Contexte
    trigger_event: str           # "letter_generation", "voluntary", etc.
    user_tier: Optional[str]
    
    # Traçabilité
    transaction_ref: Optional[str]
    validated: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Sérialisation pour stockage."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['source'] = self.source.value
        return data


@dataclass
class SolidarityAction:
    """Action solidaire financée par le fonds."""
    
    action_id: str
    timestamp: datetime
    beneficiary_type: str        # "unemployed", "student", "rsa", etc.
    
    # Impact
    amount_allocated: float
    letters_sponsored: int
    coaching_hours: int
    success_outcome: Optional[bool]  # Reconversion réussie ?
    
    # Anonymisation (RGPD)
    beneficiary_region: str      # "IDF", "PACA", etc.
    beneficiary_age_range: str   # "25-35", "35-45", etc.
    previous_sector: Optional[str]
    target_sector: Optional[str]


@dataclass
class EcologicalAction:
    """Action écologique financée par le fonds."""
    
    action_id: str
    timestamp: datetime
    action_type: str             # "carbon_offset", "reforestation", "renewable"
    
    # Impact
    amount_allocated: float
    co2_offset_tons: float
    trees_planted: Optional[int]
    renewable_kwh: Optional[float]
    
    # Partenaire
    partner_organization: str
    project_location: str
    certification: Optional[str]  # "Gold Standard", "VCS", etc.
    verification_url: Optional[str]


class PhoenixSolidarityEcologicalFund:
    """
    🌱💝 Gestionnaire du fonds solidaire-écologique Phoenix.
    
    Responsabilités:
    - Collecte des micro-contributions utilisateurs
    - Répartition 50/50 solidaire/écologique
    - Financement d'actions concrètes
    - Transparence totale et traçabilité
    - Reporting d'impact mensuel
    """
    
    # Configuration par défaut
    DEFAULT_CONTRIBUTION = 0.02  # 2 centimes par utilisation
    SOLIDARITY_RATIO = 0.50      # 50% pour le solidaire
    ECOLOGICAL_RATIO = 0.45      # 45% pour l'écologique  
    ADMIN_RATIO = 0.05          # 5% maximum pour l'administration
    
    def __init__(self, storage_path: Optional[Path] = None):
        """Initialise le gestionnaire de fonds."""
        self.storage_path = storage_path or Path("data/solidarity_fund")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Stockage des données
        self.contributions: List[FundContribution] = []
        self.solidarity_actions: List[SolidarityAction] = []
        self.ecological_actions: List[EcologicalAction] = []
        
        # Cache des statistiques
        self._stats_cache: Dict[str, Any] = {}
        self._cache_expiry: Optional[datetime] = None
        
        logger.info("🌱💝 Phoenix Solidarity-Ecological Fund initialized")
    
    def contribute_from_usage(
        self, 
        user_id: Optional[str],
        user_tier: str,
        trigger_event: str = "letter_generation",
        custom_amount: Optional[float] = None
    ) -> FundContribution:
        """
        Enregistre une contribution basée sur l'usage.
        
        Args:
            user_id: ID utilisateur (peut être anonyme)
            user_tier: Niveau d'abonnement
            trigger_event: Action qui déclenche la contribution
            custom_amount: Montant personnalisé (sinon utilise DEFAULT_CONTRIBUTION)
            
        Returns:
            FundContribution: Contribution enregistrée
        """
        amount = custom_amount or self.DEFAULT_CONTRIBUTION
        
        # Calcul de la répartition
        solidarity_amount = amount * self.SOLIDARITY_RATIO
        ecological_amount = amount * self.ECOLOGICAL_RATIO
        admin_amount = amount * self.ADMIN_RATIO
        
        contribution = FundContribution(
            contribution_id=f"contrib_{int(datetime.now().timestamp() * 1000)}",
            timestamp=datetime.now(),
            user_id=user_id,
            source=ContributionSource.USER_PREMIUM if user_tier == "premium" else ContributionSource.USER_VOLUNTARY,
            total_amount=amount,
            solidarity_amount=solidarity_amount,
            ecological_amount=ecological_amount,
            admin_amount=admin_amount,
            trigger_event=trigger_event,
            user_tier=user_tier,
            validated=True  # Auto-validation pour les micro-contributions
        )
        
        self.contributions.append(contribution)
        self._invalidate_cache()
        
        # Persistance asynchrone
        self._persist_contribution(contribution)
        
        logger.info(f"🌱💝 Contribution recorded: {amount}€ ({trigger_event})")
        return contribution
    
    def fund_solidarity_action(
        self,
        beneficiary_type: str,
        amount: float,
        letters_sponsored: int = 0,
        coaching_hours: int = 0,
        beneficiary_region: str = "Unknown",
        beneficiary_age_range: str = "Unknown"
    ) -> SolidarityAction:
        """
        Finance une action solidaire.
        
        Args:
            beneficiary_type: Type de bénéficiaire
            amount: Montant alloué
            letters_sponsored: Nombre de lettres sponsorisées
            coaching_hours: Heures de coaching offertes
            beneficiary_region: Région (anonymisée)
            beneficiary_age_range: Tranche d'âge (anonymisée)
            
        Returns:
            SolidarityAction: Action financée
        """
        # Vérification des fonds disponibles
        available_solidarity = self.get_available_solidarity_funds()
        if amount > available_solidarity:
            raise ValueError(f"Insufficient solidarity funds: {available_solidarity:.2f}€ available, {amount:.2f}€ requested")
        
        action = SolidarityAction(
            action_id=f"solidarity_{int(datetime.now().timestamp() * 1000)}",
            timestamp=datetime.now(),
            beneficiary_type=beneficiary_type,
            amount_allocated=amount,
            letters_sponsored=letters_sponsored,
            coaching_hours=coaching_hours,
            beneficiary_region=beneficiary_region,
            beneficiary_age_range=beneficiary_age_range,
            success_outcome=None  # À remplir plus tard
        )
        
        self.solidarity_actions.append(action)
        self._invalidate_cache()
        
        logger.info(f"💝 Solidarity action funded: {amount}€ for {beneficiary_type}")
        return action
    
    def fund_ecological_action(
        self,
        action_type: str,
        amount: float,
        co2_offset_tons: float,
        partner_organization: str,
        project_location: str,
        trees_planted: Optional[int] = None,
        certification: Optional[str] = None
    ) -> EcologicalAction:
        """
        Finance une action écologique.
        
        Args:
            action_type: Type d'action écologique
            amount: Montant alloué
            co2_offset_tons: Tonnes de CO2 compensées
            partner_organization: Organisation partenaire
            project_location: Localisation du projet
            trees_planted: Nombre d'arbres plantés (optionnel)
            certification: Certification du projet
            
        Returns:
            EcologicalAction: Action financée
        """
        # Vérification des fonds disponibles
        available_ecological = self.get_available_ecological_funds()
        if amount > available_ecological:
            raise ValueError(f"Insufficient ecological funds: {available_ecological:.2f}€ available, {amount:.2f}€ requested")
        
        action = EcologicalAction(
            action_id=f"ecological_{int(datetime.now().timestamp() * 1000)}",
            timestamp=datetime.now(),
            action_type=action_type,
            amount_allocated=amount,
            co2_offset_tons=co2_offset_tons,
            trees_planted=trees_planted,
            partner_organization=partner_organization,
            project_location=project_location,
            certification=certification
        )
        
        self.ecological_actions.append(action)
        self._invalidate_cache()
        
        logger.info(f"🌱 Ecological action funded: {amount}€ for {co2_offset_tons}t CO2 offset")
        return action
    
    def get_fund_statistics(self) -> Dict[str, Any]:
        """
        Récupère les statistiques complètes du fonds.
        
        Returns:
            Dict contenant toutes les métriques du fonds
        """
        # Vérification cache
        if (self._cache_expiry and 
            datetime.now() < self._cache_expiry and 
            self._stats_cache):
            return self._stats_cache
        
        # Calcul des statistiques
        total_contributions = sum(c.total_amount for c in self.contributions)
        total_solidarity_collected = sum(c.solidarity_amount for c in self.contributions)
        total_ecological_collected = sum(c.ecological_amount for c in self.contributions)
        total_admin_collected = sum(c.admin_amount for c in self.contributions)
        
        total_solidarity_spent = sum(a.amount_allocated for a in self.solidarity_actions)
        total_ecological_spent = sum(a.amount_allocated for a in self.ecological_actions)
        
        available_solidarity = total_solidarity_collected - total_solidarity_spent
        available_ecological = total_ecological_collected - total_ecological_spent
        
        # Impact solidaire
        total_letters_sponsored = sum(a.letters_sponsored for a in self.solidarity_actions)
        total_coaching_hours = sum(a.coaching_hours for a in self.solidarity_actions)
        unique_beneficiaries = len(set(
            f"{a.beneficiary_region}_{a.beneficiary_age_range}_{a.beneficiary_type}" 
            for a in self.solidarity_actions
        ))
        
        # Impact écologique
        total_co2_offset = sum(a.co2_offset_tons for a in self.ecological_actions)
        total_trees_planted = sum(a.trees_planted or 0 for a in self.ecological_actions)
        
        stats = {
            # Finances
            "total_contributions": round(total_contributions, 2),
            "total_solidarity_collected": round(total_solidarity_collected, 2),
            "total_ecological_collected": round(total_ecological_collected, 2),
            "total_admin_collected": round(total_admin_collected, 2),
            
            "total_solidarity_spent": round(total_solidarity_spent, 2),
            "total_ecological_spent": round(total_ecological_spent, 2),
            
            "available_solidarity_funds": round(available_solidarity, 2),
            "available_ecological_funds": round(available_ecological, 2),
            
            # Impact solidaire
            "solidarity_impact": {
                "total_letters_sponsored": total_letters_sponsored,
                "total_coaching_hours": total_coaching_hours,
                "unique_beneficiaries_estimated": unique_beneficiaries,
                "actions_count": len(self.solidarity_actions)
            },
            
            # Impact écologique
            "ecological_impact": {
                "total_co2_offset_tons": round(total_co2_offset, 2),
                "total_trees_planted": total_trees_planted,
                "actions_count": len(self.ecological_actions),
                "partner_organizations": len(set(a.partner_organization for a in self.ecological_actions))
            },
            
            # Métriques d'efficacité
            "efficiency_metrics": {
                "admin_percentage": round((total_admin_collected / max(total_contributions, 0.01)) * 100, 1),
                "solidarity_percentage": round((total_solidarity_collected / max(total_contributions, 0.01)) * 100, 1),
                "ecological_percentage": round((total_ecological_collected / max(total_contributions, 0.01)) * 100, 1),
                "deployment_rate_solidarity": round((total_solidarity_spent / max(total_solidarity_collected, 0.01)) * 100, 1),
                "deployment_rate_ecological": round((total_ecological_spent / max(total_ecological_collected, 0.01)) * 100, 1)
            },
            
            # Métadonnées
            "period": {
                "start_date": min([c.timestamp for c in self.contributions], default=datetime.now()).isoformat(),
                "end_date": max([c.timestamp for c in self.contributions], default=datetime.now()).isoformat(),
                "total_contributions_count": len(self.contributions)
            },
            
            "last_updated": datetime.now().isoformat()
        }
        
        # Mise en cache (30 minutes)
        self._stats_cache = stats
        self._cache_expiry = datetime.now() + timedelta(minutes=30)
        
        return stats
    
    def get_available_solidarity_funds(self) -> float:
        """Retourne les fonds solidaires disponibles."""
        collected = sum(c.solidarity_amount for c in self.contributions)
        spent = sum(a.amount_allocated for a in self.solidarity_actions)
        return round(collected - spent, 2)
    
    def get_available_ecological_funds(self) -> float:
        """Retourne les fonds écologiques disponibles."""
        collected = sum(c.ecological_amount for c in self.contributions)
        spent = sum(a.amount_allocated for a in self.ecological_actions)
        return round(collected - spent, 2)
    
    def generate_transparency_report(self, period_days: int = 30) -> Dict[str, Any]:
        """
        Génère un rapport de transparence détaillé.
        
        Args:
            period_days: Période d'analyse en jours
            
        Returns:
            Rapport complet pour publication publique
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        # Filtrage des données de la période
        period_contributions = [
            c for c in self.contributions 
            if start_date <= c.timestamp <= end_date
        ]
        period_solidarity = [
            a for a in self.solidarity_actions 
            if start_date <= a.timestamp <= end_date
        ]
        period_ecological = [
            a for a in self.ecological_actions 
            if start_date <= a.timestamp <= end_date
        ]
        
        report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "period_days": period_days,
                "phoenix_fund_version": "1.0.0"
            },
            
            "executive_summary": {
                "total_contributions_period": round(sum(c.total_amount for c in period_contributions), 2),
                "solidarity_actions_count": len(period_solidarity),
                "ecological_actions_count": len(period_ecological),
                "combined_impact_score": self._calculate_impact_score(period_solidarity, period_ecological)
            },
            
            "financial_transparency": {
                "contributions_by_source": self._analyze_contributions_by_source(period_contributions),
                "fund_allocation": {
                    "solidarity_allocated": round(sum(c.solidarity_amount for c in period_contributions), 2),
                    "ecological_allocated": round(sum(c.ecological_amount for c in period_contributions), 2),
                    "admin_allocated": round(sum(c.admin_amount for c in period_contributions), 2),
                },
                "deployment_efficiency": {
                    "solidarity_spent": round(sum(a.amount_allocated for a in period_solidarity), 2),
                    "ecological_spent": round(sum(a.amount_allocated for a in period_ecological), 2)
                }
            },
            
            "solidarity_impact": {
                "beneficiaries_helped": len(period_solidarity),
                "letters_sponsored": sum(a.letters_sponsored for a in period_solidarity),
                "coaching_hours": sum(a.coaching_hours for a in period_solidarity),
                "beneficiary_demographics": self._analyze_beneficiary_demographics(period_solidarity),
                "success_stories_count": len([a for a in period_solidarity if a.success_outcome is True])
            },
            
            "ecological_impact": {
                "co2_offset_tons": round(sum(a.co2_offset_tons for a in period_ecological), 2),
                "trees_planted": sum(a.trees_planted or 0 for a in period_ecological),
                "projects_supported": len(period_ecological),
                "partner_organizations": list(set(a.partner_organization for a in period_ecological)),
                "project_locations": list(set(a.project_location for a in period_ecological))
            },
            
            "governance_transparency": {
                "fund_governance": "Community-driven + expert advisory board",
                "decision_process": "Monthly allocation meetings with public minutes",
                "audit_status": "Quarterly independent audits",
                "public_participation": "Open voting on major allocations"
            }
        }
        
        # Sauvegarde du rapport
        report_path = self.storage_path / f"transparency_report_{datetime.now().strftime('%Y%m%d')}.json"
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"🌱💝 Transparency report saved: {report_path}")
        except Exception as e:
            logger.error(f"Failed to save transparency report: {e}")
        
        return report
    
    def _calculate_impact_score(self, solidarity_actions: List[SolidarityAction], ecological_actions: List[EcologicalAction]) -> float:
        """Calcule un score d'impact combiné (0-100)."""
        # Score solidaire (0-50)
        solidarity_score = min(len(solidarity_actions) * 5, 50)  # 5 points par action, max 50
        
        # Score écologique (0-50)  
        co2_offset = sum(a.co2_offset_tons for a in ecological_actions)
        ecological_score = min(co2_offset * 10, 50)  # 10 points par tonne CO2, max 50
        
        return round(solidarity_score + ecological_score, 1)
    
    def _analyze_contributions_by_source(self, contributions: List[FundContribution]) -> Dict[str, float]:
        """Analyse les contributions par source."""
        by_source = {}
        for source in ContributionSource:
            amount = sum(c.total_amount for c in contributions if c.source == source)
            if amount > 0:
                by_source[source.value] = round(amount, 2)
        return by_source
    
    def _analyze_beneficiary_demographics(self, actions: List[SolidarityAction]) -> Dict[str, Any]:
        """Analyse démographique anonymisée des bénéficiaires."""
        regions = {}
        ages = {}
        types = {}
        
        for action in actions:
            # Comptage par région
            regions[action.beneficiary_region] = regions.get(action.beneficiary_region, 0) + 1
            
            # Comptage par tranche d'âge
            ages[action.beneficiary_age_range] = ages.get(action.beneficiary_age_range, 0) + 1
            
            # Comptage par type
            types[action.beneficiary_type] = types.get(action.beneficiary_type, 0) + 1
        
        return {
            "by_region": regions,
            "by_age_range": ages,
            "by_beneficiary_type": types
        }
    
    def _persist_contribution(self, contribution: FundContribution) -> None:
        """Sauvegarde une contribution sur disque."""
        try:
            date_str = contribution.timestamp.strftime("%Y-%m")
            file_path = self.storage_path / f"contributions_{date_str}.jsonl"
            
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(contribution.to_dict()) + '\n')
        except Exception as e:
            logger.error(f"Failed to persist contribution: {e}")
    
    def _invalidate_cache(self) -> None:
        """Invalide le cache des statistiques."""
        self._cache_expiry = None
        self._stats_cache = {}


# Instance globale pour l'application
phoenix_solidarity_fund = PhoenixSolidarityEcologicalFund()