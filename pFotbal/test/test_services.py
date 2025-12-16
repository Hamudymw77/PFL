import unittest
from typing import List
from src.models import (
    SystemData, Player, ExerciseType, TrainingPlan, TrainingUnit,
    STATUS_PENDING, STATUS_COMPLETED
)
from src.services import DataManager, TrainingService

# --- Mocking DataManager ---

class MockDataManager(DataManager):
    """Mock version of DataManager to prevent tests from saving data to disk."""
    # Mock verze DataManageru, aby testy neukladaly data na disk.
    # نسخة وهمية من مدير البيانات لمنع الاختبارات من حفظ البيانات على القرص
    def __init__(self, system_data):
        self._system_data = system_data
        
    def save_data(self, system_data: SystemData):
        """Simulates saving data without writing to file."""
        # Simuluje ukladani dat bez zapisu do souboru.
        # يحاكي حفظ البيانات دون الكتابة في ملف
        self._system_data = system_data
        
    def _get_next_id(self, entity_list: List):
        """Generates a unique ID based on the current list maximum."""
        # Generuje unikatni ID na zaklade maxima v aktualnim seznamu.
        # ينشئ معرفًا فريدًا بناءً على الحد الأقصى للقائمة الحالية
        if not entity_list:
            return 1
        return max([e.id for e in entity_list if hasattr(e, 'id')], default=0) + 1

# --- Test Suite ---

class TestTrainingService(unittest.TestCase):
    
    def setUp(self):
        """Setup test data before each test."""
        # Nastaveni testovacich dat pred kazdym testem.
        # إعداد بيانات الاختبار قبل كل اختبار
        self.system_data = SystemData()
        
        # Pridej hrace 101 a 102
        # أضف اللاعبين 101 و 102
        self.system_data.players.append(Player(id=101, name="Lukas Novak", position="Midfielder"))
        self.system_data.players.append(Player(id=102, name="Tomas Svoboda", position="Forward"))

        # Typy Cviceni (predem nactene v DataManager mock setupu)
        # أنواع التمارين
        self.system_data.exercise_types = [
            ExerciseType(code="SPRINT", description="Running", parameters_metadata={"distance_m": "float", "repetitions": "int"}),
            ExerciseType(code="SHOOT", description="Shooting practice", parameters_metadata={"shots_taken": "int", "goals_scored": "int"}),
        ]
        
        # Vytvor vzorovy plan (Plan ID 1) pro Hraci 101
        # إنشاء خطة نموذجية للاعب 101
        plan_id = 1
        self.plan1 = TrainingPlan(id=plan_id, player_id=101, date_assigned="2025-12-01", status=STATUS_PENDING)
        self.system_data.training_plans.append(self.plan1)

        # Pridej dve jednotky do Planu 1
        # أضف وحدتين إلى الخطة 1
        self.unit1_1 = TrainingUnit(id=1, type_code="SPRINT", specific_parameters={"distance_m": 50.0, "repetitions": 10})
        self.unit1_2 = TrainingUnit(id=2, type_code="SHOOT", specific_parameters={"shots_taken": 20, "goals_scored": 12})
        self.plan1.exercises.extend([self.unit1_1, self.unit1_2])

        # Inicializuj Sluzby
        # تهيئة الخدمات
        self.dm_mock = MockDataManager(self.system_data)
        self.ts = TrainingService(self.dm_mock)
        
    def test_find_player(self):
        """Tests player lookup by ID."""
        # Testuje vyhledavani hrace podle ID.
        # اختبار البحث عن لاعب بواسطة المعرف
        player = self.ts.find_player(self.system_data, 101)
        self.assertIsNotNone(player)
        self.assertEqual(player.name, "Lukas Novak")
        
        player_not_found = self.ts.find_player(self.system_data, 999)
        self.assertIsNone(player_not_found)

    def test_add_exercise_to_plan_success(self):
        """Tests adding a new unit to an existing plan."""
        # Testuje pridani nove jednotky do existujiciho planu.
        # اختبار إضافة وحدة جديدة إلى خطة موجودة
        new_unit = self.ts.add_exercise_to_plan(
            self.system_data, 1, "SHOOT", {"shots_taken": 15, "goals_scored": 8}
        )
        self.assertIsNotNone(new_unit)
        self.assertEqual(len(self.plan1.exercises), 3)
        self.assertEqual(new_unit.id, 3) # IDs are generated sequentially

    def test_add_exercise_to_plan_invalid_params(self):
        """Tests error handling when required parameters are missing."""
        # Testuje osetreni chyby, kdyz chybi pozadovane parametry.
        # اختبار معالجة الأخطاء عند فقدان المعلمات المطلوبة
        with self.assertRaises(ValueError):
             self.ts.add_exercise_to_plan( # Missing 'distance_m' for SPRINT
                self.system_data, 1, "SPRINT", {"repetitions": 5}
            )

    def test_mark_exercise_completed_and_plan_status(self):
        """Tests marking a unit as completed and checks plan status update."""
        # Testuje oznaceni jednotky jako dokonceno a kontroluje aktualizaci stavu planu.
        # اختبار وضع علامة على الوحدة كمكتملة والتحقق من تحديث حالة الخطة
        
        # Oznac prvni jednotku (ID 1) jako dokonceno
        # ضع علامة على الوحدة الأولى (ID 1) كمكتملة
        success = self.ts.mark_exercise_completed(self.system_data, 1, 1)
        self.assertTrue(success)
        self.assertEqual(self.unit1_1.specific_parameters.get('status'), STATUS_COMPLETED)
        self.assertEqual(self.plan1.status, STATUS_PENDING) # Still pending because unit 2 is incomplete

        # Oznac druhou jednotku (ID 2) jako dokonceno
        # ضع علامة على الوحدة الثانية (ID 2) كمكتملة
        success = self.ts.mark_exercise_completed(self.system_data, 1, 2)
        self.assertTrue(success)
        
        # Zkontroluj, zda je cely plan nyni oznacen jako DOKONCENO
        # تحقق مما إذا كانت الخطة بأكملها تحمل الآن علامة "مكتمل"
        self.assertEqual(self.plan1.status, STATUS_COMPLETED)

    def test_get_plan_summary(self):
        """Tests the calculation of completion summary."""
        # Testuje vypocet souhrnu dokonceni.
        # اختبار حساب ملخص الإكمال
        
        # Initial status: 0/2 completed
        summary_initial = self.ts.get_plan_summary(self.plan1)
        self.assertEqual(summary_initial["total"], 2)
        self.assertEqual(summary_initial["completed"], 0)
        self.assertEqual(summary_initial["completion_percentage"], "0.0%")
        
        # Oznac jednu jednotku jako dokonceno
        # ضع علامة على وحدة واحدة كمكتملة
        self.ts.mark_exercise_completed(self.system_data, 1, 1)
        
        # Final status: 1/2 completed
        summary_final = self.ts.get_plan_summary(self.plan1)
        self.assertEqual(summary_final["completed"], 1)
        self.assertEqual(summary_final["pending"], 1)
        self.assertEqual(summary_final["completion_percentage"], "50.0%")
        
        
if __name__ == '__main__':
    unittest.main()