from typing import Any, Literal

from pydantic import BaseModel, Field


PriorityLevel = Literal["High", "Medium", "Low"]
SeverityLevel = Literal["HIGH", "MEDIUM", "LOW"]
CategoryType = Literal["Visual", "Audio", "Pacing", "Metadata", "Structure"]


class Evidence(BaseModel):
    ei: float = Field(..., description="Final emotional intensity score, normalized 0-1.")
    audio_energy: float = Field(..., description="Soundtrack/audio energy score, normalized 0-1.")
    motion: float = Field(..., description="Motion intensity score, normalized 0-1.")
    object_score: float = Field(..., description="Visual object/scene impact score, normalized 0-1.")
    emotion_confidence: float = Field(..., description="Facial or visual emotion confidence, normalized 0-1.")
    scene_type: str
    scene_type_confidence: float = Field(default=1.0, description="ML scene-type classifier confidence, 0-1.")
    classification_reliable: bool = Field(default=True, description="Whether scene classification is reliable.")
    visual_emotion: str
    audio_mood: str
    act: str = Field(
        default="unknown",
        description=(
            "Position of this scene in the trailer's five-phase structure: opening_hook, introduction, "
            "build_up, climax, or resolution."
        ),
    )
    audio_emotion: str = Field(default="unknown", description="ML-predicted audio emotion class (distinct from audio_mood).")
    tempo_bpm: float = Field(default=0.0, description="Estimated musical tempo in beats per minute.")
    mfcc_mean: float = Field(default=0.0, description="Mean MFCC coefficient across the scene's audio window.")
    spectral_centroid: float = Field(default=0.0, description="Mean spectral centroid frequency (Hz) of the scene's audio.")
    shot_duration: float = Field(default=0.0, description="Duration of this scene/shot in seconds.")
    objects: str = Field(default="", description="Comma-separated objects detected in this scene (YOLO).")


class TimelineInsight(BaseModel):
    scene: int
    timeframe: str
    intensity_level: str
    strongest_signal: str
    weakest_signal: str
    evidence: Evidence


class Recommendation(BaseModel):
    id: str | int
    scene: int
    scene_label: str = ""
    timeframe: str
    phase: str = ""
    problem: str
    recommendation: str
    reason: str
    reasoning: str = ""
    strengths: list[str] = Field(default_factory=list)
    problems: list[str] = Field(default_factory=list)
    expected_improvement: str = ""
    focus_area: str
    priority_score: int
    priority: PriorityLevel
    evidence: Evidence

    # Frontend-aligned & professional editorial fields
    title: str = ""
    action: str = ""
    evidence_text: str = ""
    category: CategoryType = "Visual"
    priority_num: int = 1
    component: str = "Component 04 - Emotional Intensity Fusion"
    expected_impact: str = ""

    # New evidence-based fields (additive — backward compatible)
    severity: SeverityLevel = "MEDIUM"
    confidence: float = Field(default=0.5, description="Recommendation confidence 0-1.")
    evidence_details: dict[str, Any] = Field(default_factory=dict, description="Structured evidence supporting this recommendation.")
    start_time: float | None = Field(default=None, description="Exact start time in seconds.")
    end_time: float | None = Field(default=None, description="Exact end time in seconds.")
    why: str = Field(default="", description="Why this matters for the trailer.")
    fix_source: str = Field(
        default="template",
        description="Source of the displayed wording (gemini, anthropic, local-dynamic, or the detector itself). Detector provenance remains in evidence_details.detector_source.",
    )


class RecommendationSummary(BaseModel):
    trailer_title: str
    total_scenes: int
    average_emotional_intensity: float
    weakest_timeframe: str | None = None
    strongest_timeframe: str | None = None
    main_problem: str
    overall_recommendation: str
    overall_reaction: str = "Moderate"
    popularity_reaction: str | None = None
    popularity_score: float | None = None
    engagement_rate: float | None = None
    recommendation_model: str | None = None
    recommendation_model_version: str | None = None
    mean_prediction_confidence: float | None = None


class PopularityContext(BaseModel):
    predicted_reaction: str | None = None
    confidence_score: float | None = None
    popularity_score: float | None = None
    engagement_rate: float | None = None
    model_version: str | None = None


class SentimentContext(BaseModel):
    """Audience comment sentiment data fetched from the analyses Firestore collection."""
    trailer_id: str | None = None
    trailer_title: str | None = None
    positive_pct: float | None = None
    negative_pct: float | None = None
    neutral_pct: float | None = None
    dominant_emotion: str | None = None
    emotion_distribution: dict[str, float] = Field(default_factory=dict)
    top_topics: list[str] = Field(default_factory=list)
    total_comments: int | None = None
    model_used: str | None = None
    model_accuracy: float | None = None
    sentiment_label: str | None = None


class ComponentScores(BaseModel):
    audio: int = 85
    visual: int = 90
    metadata: int = 80
    fusion: int = 88


class TimingRoadmapItem(BaseModel):
    timeframe: str
    scene: str
    currentEmotion: str
    suggestion: str
    priority: int


class RecommendationRequest(BaseModel):
    source_prediction_id: str | None = None
    trailer_title: str | None = None
    trailer_id: str | None = None
    insights: dict[str, Any] = Field(default_factory=dict)
    final_system_output: list[dict[str, Any]] = Field(default_factory=list)
    audio_feature_output: list[dict[str, Any]] = Field(default_factory=list)
    visual_feature_output: list[dict[str, Any]] = Field(default_factory=list)
    popularity_context: PopularityContext | None = None
    trailer_output_dir: str | None = Field(
        default=None,
        description="Path to this trailer's storage/outputs/<slug> folder, if scene thumbnails are available there. Enables frame-level checks (logo placement, on-screen title/release-date) — silently skipped when absent.",
    )


# ── New models for the enhanced recommendation engine ──────────────────────


class TrailerProfile(BaseModel):
    """Trailer-level genre classification with probabilities."""
    primary_genre: str
    secondary_genres: list[str] = Field(default_factory=list)
    genre_probabilities: dict[str, float] = Field(default_factory=dict)
    genre_confidence: float = Field(default=0.5, description="Overall confidence in genre classification 0-1.")
    genre_source: str = Field(
        default="rule-based",
        description=(
            "How the genre was determined: 'lmtd-real-ml' when the real "
            "LMTD-9-trained model ran on fetched movie metadata, or "
            "'rule-based-fallback' when metadata wasn't available and the "
            "hand-authored scene-evidence classifier was used instead."
        ),
    )


class DistributionStats(BaseModel):
    """Statistical distribution summary for a single metric."""
    median: float = 0.0
    mean: float = 0.0
    std: float = 0.0
    q1: float = 0.0
    q3: float = 0.0
    iqr: float = 0.0
    min_val: float = 0.0
    max_val: float = 0.0
    values: list[float] = Field(default_factory=list, description="Per-scene values in temporal order.")


class TrailerBaseline(BaseModel):
    """Per-trailer statistical baseline used for anomaly detection.

    All anomalies are measured relative to this trailer's own distributions,
    not against universal thresholds.
    """
    total_scenes: int = 0
    total_duration: float = 0.0
    shot_duration: DistributionStats = Field(default_factory=DistributionStats)
    motion: DistributionStats = Field(default_factory=DistributionStats)
    audio_energy: DistributionStats = Field(default_factory=DistributionStats)
    tempo: DistributionStats = Field(default_factory=DistributionStats)
    ei: DistributionStats = Field(default_factory=DistributionStats)
    scene_type_distribution: dict[str, float] = Field(default_factory=dict, description="Confidence-weighted scene-type proportions.")
    audio_mood_distribution: dict[str, float] = Field(default_factory=dict)
    face_emotion_distribution: dict[str, float] = Field(default_factory=dict)
    escalation_gradient: float = Field(default=0.0, description="Positive = intensity increases over time.")
    pacing_curve: list[float] = Field(default_factory=list, description="Combined energy per scene in temporal order.")


class StructuralPhase(BaseModel):
    """A detected structural segment of the trailer."""
    phase_name: str = Field(description="e.g., setup, buildup, peak, cooldown, resolution")
    start_scene: int = 0
    end_scene: int = 0
    start_pct: float = 0.0
    end_pct: float = 0.0
    avg_energy: float = 0.0
    confidence: float = 0.5


# ── Existing models kept for compatibility ─────────────────────────────────


class RecommendationResponse(BaseModel):
    # Core response
    summary: RecommendationSummary
    timeline_insights: list[TimelineInsight]
    recommendations: list[Recommendation]
    popularity_context: PopularityContext | None = None
    sentiment_context: SentimentContext | None = None
    model_metrics: dict[str, Any] | None = None
    source: str = "recommendation-engine"
    source_prediction_id: str | None = None
    recommendation_id: str | None = None
    created_at: str | None = None

    # Top-level direct frontend compatibility fields
    id: str | None = None
    trailerTitle: str | None = None
    sourceUrl: str | None = None
    generatedAt: str | None = None
    overallPriorityScore: int = 85
    modelConfidence: int = 92
    focusArea: str = "Pacing & Audio Dynamics"
    targetAudienceReach: int = 82
    componentScores: ComponentScores = Field(default_factory=ComponentScores)
    timings: list[TimingRoadmapItem] = Field(default_factory=list)

    # New enhanced fields (additive — backward compatible)
    trailer_profile: TrailerProfile | None = None
    trailer_baseline: TrailerBaseline | None = None
    structural_phases: list[StructuralPhase] = Field(default_factory=list)


class TrailerMeta(BaseModel):
    total_duration: float
    trailer_type: Literal["teaser", "theatrical", "tv_spot", "unknown"]

class SceneDiagnosis(BaseModel):
    scene_id: int
    scene_intent: str
    focus_area: str
    problem: str
    is_problem: bool
    evidence: dict[str, Any]
    severity: float
    beat: str = "none"
    beat_confidence: float = 0.0
    genre_probs: dict[str, float] = {}
    is_gutpunch_line: bool = False

class StructureReport(BaseModel):
    has_hook: bool
    has_logo: bool
    has_climax: bool
    has_button: bool
    logo_position: Literal["start","end","none"]
    climax_position_pct: float
    structure_confidence: float
    detected_beats: dict[str, float] = {}
    signature_moment: dict[str, Any] = {}
    phases: list[StructuralPhase] = Field(default_factory=list)

class GenreReport(BaseModel):
    trailer_mixture: dict[str, float]
    genre_curve: list[dict[str, float]]
    dominant_genre: str
    secondary_genre: str | None = None
    secondary_genres: list[str] = Field(default_factory=list)
    genre_confidence: float = Field(default=0.5)
    genre_probabilities: dict[str, float] = Field(default_factory=dict)
    genre_source: str = Field(
        default="rule-based",
        description="'lmtd-real-ml' when the real LMTD-9-trained model produced this, 'rule-based-fallback' otherwise.",
    )
