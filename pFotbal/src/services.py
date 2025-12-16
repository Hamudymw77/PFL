# src/services.py
import json
import os
from datetime import date
from typing import List, Optional, Dict, Any
from dataclasses import asdict, is_dataclass
# IMPORTY PRO PARALELISMUS
import threading
from functools import wraps 

from config import DATA_FILE_PATH
from src.models import (
    SystemData, Player, ExerciseType, TrainingPlan, TrainingUnit,
    STATUS_PENDING, STATUS_COMPLETED
)

# --- Dekorátor pro Paralelismus ---
def run_in_thread(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Spustime ulozeni v novem vlakne na pozadi.
        # We start saving in a new background thread.
        # نبدأ الحفظ في خيط خلفي جديد
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper

# Helper class for JSON serialization
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if is_dataclass(o):
            return asdict(o)
        return super().default(o)

class DataManager:
    """Handles saving and loading the SystemData object."""
    # Stara se o ukladani a nacitani SystemData objektu.
    # يتعامل مع حفظ وتحميل كائن بيانات النظام
    
    def _create_empty_data_if_needed(self):
        """Creates initial data file and structure."""
        # Vytvori pocatecni datovy soubor a strukturu.
        # ينشئ ملف وهيكل بيانات أولي
        if not os.path.exists(os.path.dirname(DATA_FILE_PATH)):
            os.makedirs(os.path.dirname(DATA_FILE_PATH))
            
        if not os.path.exists(DATA_FILE_PATH):
            initial_data = SystemData(
                exercise_types=[
                    # Vychozi typy cviceni
                    ExerciseType(code="SPRINT", description="Short distance running training.", parameters_metadata={"distance_m": "float", "repetitions": "int"}),
                    ExerciseType(code="SHOOT", description="Goal shooting practice.", parameters_metadata={"shots_taken": "int", "goals_scored": "int"}),
                    ExerciseType(code="JUMP", description="Vertical or horizontal jumping drills.", parameters_metadata={"jumps_count": "int", "height_cm": "float"}),
                ]
            )
            self.save_data(initial_data)
            return True
        return True

    def load_data(self) -> SystemData:
        """Loads data from file and performs deserialization."""
        # Nacte data ze souboru.
        # يحمل البيانات من الملف
        self._create_empty_data_if_needed()
        with open(DATA_FILE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Manual deserialization
        players = [Player(**p) for p in data.pop('players', [])]
        exercise_types = [ExerciseType(**e) for e in data.pop('exercise_types', [])]
        
        training_plans = []
        for p_data in data.pop('training_plans', []):
            exercises = [TrainingUnit(**e) for e in p_data.pop('exercises', [])]
            plan = TrainingPlan(**p_data)
            plan.exercises = exercises
            training_plans.append(plan)

        return SystemData(
            players=players,
            exercise_types=exercise_types,
            training_plans=training_plans
        )

    @run_in_thread
    def save_data(self, system_data: SystemData):
        """Saves the current state of SystemData object to JSON file in a separate thread (PARALLELISM)."""
        # Ulozi data do JSON souboru v samostatnem vlakne (PARALELISMUS).
        # يحفظ البيانات في ملف JSON في خيط منفصل (توازي)
        try:
            with open(DATA_FILE_PATH, 'w', encoding='utf-8') as f:
                # TISK pro demonstraci vlakna
                print("[INFO: ASYNC SAVE START] Saving data in background thread...")
                json.dump(asdict(system_data), f, ensure_ascii=False, indent=4, cls=JSONEncoder)
                print("[INFO: ASYNC SAVE END] Data saved successfully.")
        except Exception as e:
            print(f"[ERROR: ASYNC SAVE FAILED] Could not save data: {e}")

    def _get_next_id(self, entity_list: List):
        """Helper method to generate a unique ID."""
        # Pomocna metoda pro generovani unikatniho ID.
        return max([e.id for e in entity_list], default=0) + 1

    def add_player(self, system_data: SystemData, name: str, position: str) -> Player:
        """Adds a new player to the system."""
        new_player = Player(
            id=self._get_next_id(system_data.players),
            name=name,
            position=position
        )
        system_data.players.append(new_player)
        self.save_data(system_data) # Asynchronni ukladani
        return new_player

class TrainingService:
    """Contains business logic for managing exercises and plans."""
    # Obsahuje obchodni logiku.
    
    def __init__(self, dm: DataManager):
        self.dm = dm

    # ... (Ostatní metody TrainingService pro create_training_plan, add_exercise_to_plan, mark_exercise_completed, get_plan_summary) ...
    
    def find_player(self, system_data: SystemData, player_id: int) -> Optional[Player]:
        return next((p for p in system_data.players if p.id == player_id), None)
        
    def find_exercise_type(self, system_data: SystemData, code: str) -> Optional[ExerciseType]:
        return next((e for e in system_data.exercise_types if e.code == code), None)

    def find_plan(self, system_data: SystemData, plan_id: int) -> Optional[TrainingPlan]:
        return next((p for p in system_data.training_plans if p.id == plan_id), None)
        
    def create_training_plan(
        self, system_data: SystemData, player_id: int, target_date: Optional[str]
    ) -> Optional[TrainingPlan]:
        if not self.find_player(system_data, player_id): return None
        new_plan = TrainingPlan(
            id=self.dm._get_next_id(system_data.training_plans),
            player_id=player_id,
            date_assigned=date.today().isoformat(),
            target_completion_date=target_date,
            status=STATUS_PENDING
        )
        system_data.training_plans.append(new_plan)
        self.dm.save_data(system_data)
        return new_plan

    def add_exercise_to_plan(
        self, system_data: SystemData, plan_id: int, type_code: str, params: Dict[str, Any]
    ) -> Optional[TrainingUnit]:
        plan = self.find_plan(system_data, plan_id)
        exercise_type = self.find_exercise_type(system_data, type_code)
        if not plan or not exercise_type: return None
        if not all(key in params for key in exercise_type.parameters_metadata.keys()):
            raise ValueError("Missing parameters for the selected exercise type.")
            
        all_units = [u for p in system_data.training_plans for u in p.exercises]
        unit_id = self.dm._get_next_id(all_units)

        new_unit = TrainingUnit(
            id=unit_id,
            type_code=type_code,
            specific_parameters=params
        )
        plan.exercises.append(new_unit)
        self.dm.save_data(system_data)
        return new_unit
        
    def mark_exercise_completed(self, system_data: SystemData, plan_id: int, unit_id: int) -> bool:
        plan = self.find_plan(system_data, plan_id)
        if not plan: return False
            
        unit_to_update = next((u for u in plan.exercises if u.id == unit_id), None)
        if not unit_to_update: return False

        unit_to_update.specific_parameters['status'] = STATUS_COMPLETED
        
        is_plan_fully_completed = all(u.specific_parameters.get('status') == STATUS_COMPLETED for u in plan.exercises)
        if is_plan_fully_completed:
            plan.status = STATUS_COMPLETED
            
        self.dm.save_data(system_data)
        return True
        
    def get_plan_summary(self, plan: TrainingPlan) -> Dict[str, Any]:
        total_units = len(plan.exercises)
        completed_units = sum(1 for u in plan.exercises if u.specific_parameters.get('status') == STATUS_COMPLETED)
        
        return {
            "total": total_units,
            "completed": completed_units,
            "pending": total_units - completed_units,
            "completion_percentage": f"{completed_units / total_units * 100:.1f}%" if total_units > 0 else "N/A"
        }