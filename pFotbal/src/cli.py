# src/cli.py
import sys
import os

# Oprava chyby importu (ModuleNotFoundError)
try:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if project_root not in sys.path:
        sys.path.append(project_root)
except Exception:
    pass

from src.services import DataManager, TrainingService
from src.models import STATUS_COMPLETED, STATUS_PENDING, SystemData, ExerciseType
from typing import Optional

# Initial setup
class TrainingPlannerCLI:
    """Command Line Interface for the Training Planner."""
    # Rozhrani prikazove radky.
    
    def __init__(self):
        self.dm = DataManager()
        self.ts = TrainingService(self.dm)
        self.system_data: Optional[SystemData] = None
        
        try:
            self.dm._create_empty_data_if_needed() 
            self.system_data = self.dm.load_data()
        except Exception as e:
            print(f"ERROR: Failed to load system data. {e}")
            sys.exit(1)
            
        print("\n=== WELCOME TO THE TRAINING PLANNER CLI (Trainer Mode) ===")

    def display_menu(self):
        """Displays the main menu options."""
        print("\n--- MAIN MENU ---")
        print("1. View Player List & Current Plans")
        print("2. Add New Player")
        print("3. Define New Exercise Type")
        print("4. Create and Assign New Training Plan")
        print("5. Mark Exercise as Completed in a Plan")
        print("0. Exit")

    def run(self):
        """Main program loop."""
        while True:
            self.display_menu()
            choice = input("Enter choice (0-5): ").strip()
            
            try:
                if choice == '1': self.view_players_and_plans()
                elif choice == '2': self.add_player()
                elif choice == '3': self.define_exercise_type()
                elif choice == '4': self.create_and_assign_plan()
                elif choice == '5': self.mark_exercise_completed()
                elif choice == '0':
                    print("Exiting Planner. Goodbye!")
                    break
                else:
                    print("Invalid choice, please try again.")
            except ValueError as e:
                 print(f"\nERROR: Invalid input format. {e}")
            except Exception as e:
                print(f"\nCRITICAL ERROR: An unexpected error occurred: {e}")

    # --- Implementation of Menu Options (zkraceno, logika je v services) ---
    def view_players_and_plans(self):
        if not self.system_data.players: print("No players registered."); return
        print("\n--- PLAYER LIST & PENDING PLANS ---")
        for player in self.system_data.players:
            print(f"\n[ID {player.id}] {player.name} ({player.position})")
            player_plans = [p for p in self.system_data.training_plans if p.player_id == player.id and p.status == STATUS_PENDING]
            if player_plans:
                print("  PENDING PLANS:")
                for plan in player_plans:
                    summary = self.ts.get_plan_summary(plan)
                    print(f"    - PLAN ID {plan.id}: Assigned {plan.date_assigned} (Target: {plan.target_completion_date or 'N/A'})")
                    print(f"      Status: {summary['completed']}/{summary['total']} completed ({summary['completion_percentage']})")
            else:
                print("  No pending plans.")

    def add_player(self):
        print("\n--- ADD NEW PLAYER ---")
        name = input("Enter player's name: ").strip(); position = input("Enter player's position: ").strip()
        if not name or not position: print("ERROR: Name and position cannot be empty."); return
        new_player = self.ts.dm.add_player(self.system_data, name, position)
        print(f"Player '{new_player.name}' (ID {new_player.id}) successfully added.")
        
    def define_exercise_type(self):
        print("\n--- DEFINE NEW EXERCISE TYPE ---")
        print("Existing Types:"); 
        for et in self.system_data.exercise_types:
            params = [f"{k} ({v})" for k, v in et.parameters_metadata.items()]
            print(f"- {et.code} ({et.description}) [Needs: {', '.join(params)}]")
            
        code = input("Enter unique CODE (e.g., TACKLE): ").strip().upper()
        description = input("Enter description: ").strip()
        
        if self.ts.find_exercise_type(self.system_data, code):
            print(f"ERROR: Exercise Type with code '{code}' already exists."); return

        param_str = input("Enter parameters (e.g., 'reps:int, distance_m:float'): ").strip()
        metadata = {}; valid_input = True
        try:
            if param_str:
                for p in param_str.split(','):
                    key, dtype = p.split(':'); metadata[key.strip()] = dtype.strip()
        except ValueError:
            print("ERROR: Invalid parameter format. Use 'key:type, key2:type2'."); return
            
        new_type = ExerciseType(code=code, description=description, parameters_metadata=metadata)
        self.system_data.exercise_types.append(new_type); self.ts.dm.save_data(self.system_data)
        print(f"New exercise type '{code}' successfully defined.")

    def create_and_assign_plan(self):
        self.view_players_and_plans()
        if not self.system_data.players: return
        try: player_id = int(input("\nEnter Player ID to assign plan to: ").strip())
        except ValueError: print("ERROR: Player ID must be a number."); return
        player = self.ts.find_player(self.system_data, player_id)
        if not player: print("ERROR: Player not found."); return
            
        target_date = input("Enter Target Completion Date (YYYY-MM-DD, or leave blank): ").strip() or None
        new_plan = self.ts.create_training_plan(self.system_data, player_id, target_date)
        if not new_plan: print("ERROR: Failed to create plan."); return
            
        print(f"Plan ID {new_plan.id} created for {player.name}. Now adding exercises...")
        
        while True:
            print("\nAvailable Exercise Types:"); 
            for et in self.system_data.exercise_types:
                params = [f"{k} ({v})" for k, v in et.parameters_metadata.items()]; print(f"- CODE: {et.code} ({et.description}) [Needs: {', '.join(params)}]")
                
            type_code = input("Enter Exercise CODE to add (or 'DONE' to finish): ").strip().upper()
            if type_code == 'DONE': break
                
            ex_type = self.ts.find_exercise_type(self.system_data, type_code)
            if not ex_type: print("Invalid exercise code."); continue

            params = {}; valid_input = True
            for key, dtype in ex_type.parameters_metadata.items():
                val = input(f"  Enter value for {key} ({dtype}): ").strip()
                try:
                    if dtype == 'int': params[key] = int(val)
                    elif dtype == 'float': params[key] = float(val)
                    else: params[key] = val
                except ValueError: print(f"ERROR: Invalid format for {key}. Expected {dtype}."); valid_input = False; break
            
            if valid_input:
                try: self.ts.add_exercise_to_plan(self.system_data, new_plan.id, type_code, params)
                except ValueError as e: print(f"ERROR: Could not add exercise. {e}")
                print(f"Exercise '{type_code}' added to Plan {new_plan.id}.")
                
        print(f"\nTraining Plan {new_plan.id} finalized for {player.name}.")

    def mark_exercise_completed(self):
        print("\n--- MARK EXERCISE COMPLETED ---")
        found_pending = False
        for plan in self.system_data.training_plans:
            if plan.status == STATUS_PENDING:
                found_pending = True
                player = self.ts.find_player(self.system_data, plan.player_id)
                pending_units = [u for u in plan.exercises if u.specific_parameters.get('status') != STATUS_COMPLETED]
                
                if pending_units:
                    print(f"\nPLAN ID {plan.id} for {player.name if player else 'Unknown Player'}:")
                    for unit in pending_units: print(f"  [UNIT ID {unit.id}] {unit.type_code} (Params: {unit.specific_parameters})")

        if not found_pending: print("No pending training plans found."); return

        try:
            plan_id = int(input("\nEnter Plan ID: ").strip())
            unit_id = int(input("Enter Unit ID to mark as Completed: ").strip())
        except ValueError: print("ERROR: ID must be a number."); return

        if self.ts.mark_exercise_completed(self.system_data, plan_id, unit_id):
            print(f"Unit ID {unit_id} in Plan {plan_id} marked as COMPLETED.")
        else:
            print("ERROR: Plan or Unit ID not found, or unit is already completed.")


if __name__ == "__main__":
    cli = TrainingPlannerCLI()
    cli.run()