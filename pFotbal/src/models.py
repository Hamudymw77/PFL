
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

# Konstanty pro stav treninkoveho planu
# ثوابت لحالة خطة التدريب
STATUS_PENDING = "Pending"
STATUS_COMPLETED = "Completed"
STATUS_CANCELLED = "Cancelled"

@dataclass
class Player:
    """Represents a football player."""
    # Reprezentuje fotbaloveho hrace.
    # يمثل لاعب كرة قدم
    id: int = field(default_factory=lambda: 0)
    name: str = ""
    position: str = ""

@dataclass
class ExerciseType:
    """Defines a standardized type of exercise (Sprint, Shooting, etc.)."""
    # Definuje standardizovany typ cviceni.
    # يحدد نوعًا موحدًا من التمارين
    code: str = "" 
    description: str = ""
    parameters_metadata: Dict[str, str] = field(default_factory=dict) 

@dataclass
class TrainingUnit:
    """A specific exercise instance within a plan."""
    # Konkretni instance cviceni v ramci planu.
    # مثيل تمرين محدد ضمن الخطة
    id: int = field(default_factory=lambda: 0)
    type_code: str = ""
    specific_parameters: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TrainingPlan:
    """The entire plan assigned to a player."""
    # Cely plan prirazeny hraci.
    # الخطة الكاملة المخصصة للاعب
    id: int = field(default_factory=lambda: 0)
    player_id: int = 0
    date_assigned: str = ""
    target_completion_date: Optional[str] = None
    exercises: List[TrainingUnit] = field(default_factory=list)
    status: str = STATUS_PENDING
    
@dataclass
class SystemData:
    """Main container for storing all data."""
    # Hlavni kontejner pro ulozeni vsech dat.
    # الحاوية الرئيسية لتخزين كافة البيانات
    players: List[Player] = field(default_factory=list)
    exercise_types: List[ExerciseType] = field(default_factory=list)

    training_plans: List[TrainingPlan] = field(default_factory=list)
