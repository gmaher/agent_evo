import sys
import os
sys.path.append(os.path.abspath(".."))

import argparse
import shutil
from pathlib import Path
from datetime import datetime
import json
from agent_evo.core.app import AgentEvoApp
from agent_evo.prompts.builder import CREATE_FACTORY_TASK


def main():
    parser = argparse.ArgumentParser(
        description="Create initial population of AI factory teams"
    )
    parser.add_argument(
        "--template-dir",
        required=True,
        help="Template directory containing /team and /tasks folders"
    )
    parser.add_argument(
        "--builder-dir",
        required=True,
        help="Directory containing builder team files (agents.json and team.json)"
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory to create population folders"
    )
    parser.add_argument(
        "--population-size",
        type=int,
        default=5,
        help="Number of factory teams to create (K)"
    )
    parser.add_argument("--model", default="gpt-4o", help="LLM model to use")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    try:
        template_dir = Path(args.template_dir)
        builder_dir = Path(args.builder_dir)
        output_dir = Path(args.output_dir)
        
        # Validate template directory
        if not template_dir.exists():
            raise FileNotFoundError(f"Template directory not found: {template_dir}")
        
        team_folder = template_dir / "team"
        tasks_folder = template_dir / "tasks"
        
        if not team_folder.exists():
            raise FileNotFoundError(f"Template must contain /team folder: {team_folder}")
        if not tasks_folder.exists():
            raise FileNotFoundError(f"Template must contain /tasks folder: {tasks_folder}")
        
        # Validate builder directory has required files
        if not builder_dir.exists():
            raise FileNotFoundError(f"Builder directory not found: {builder_dir}")
        
        if not (builder_dir / "agents.json").exists():
            raise FileNotFoundError(f"Builder directory must contain agents.json")
        if not (builder_dir / "team.json").exists():
            raise FileNotFoundError(f"Builder directory must contain team.json")
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save metadata
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "template_dir": str(template_dir),
            "builder_dir": str(builder_dir),
            "population_size": args.population_size,
            "model": args.model,
            "populations": []
        }
        
        print(f"{'='*60}")
        print(f"INITIAL POPULATION SETUP")
        print(f"{'='*60}")
        print(f"Template: {template_dir}")
        print(f"Builder: {builder_dir}")
        print(f"Output: {output_dir}")
        print(f"Population size: {args.population_size}")
        print(f"Model: {args.model}")
        print(f"{'='*60}\n")
        
        # Create each population member
        for i in range(args.population_size):
            print(f"\n{'='*60}")
            print(f"CREATING POPULATION MEMBER {i}/{args.population_size}")
            print(f"{'='*60}")
            
            # Create population directory
            pop_dir = output_dir / f"population_{i}"
            
            if args.verbose:
                print(f"Copying template to: {pop_dir}")
            
            # Copy template directory
            if pop_dir.exists():
                shutil.rmtree(pop_dir)
            shutil.copytree(template_dir, pop_dir)
            
            # Path for generated team (agents.json and team.json will be created here)
            team_output_dir = pop_dir / "team"
            
            if args.verbose:
                print(f"Team will be generated in: {team_output_dir}")
                print(f"Expected output: agents.json, team.json")
            
            try:
                # Initialize app for this population member
                # Use empty ignored_files so builder can see all context
                app = AgentEvoApp(
                    model=args.model,
                    output_dir=str(team_output_dir),
                    ignored_files=[]
                )
                
                # Load builder team
                builder_config = app.load_team_from_directory(str(builder_dir))
                
                if args.verbose:
                    print(f"Loaded builder team: {builder_config['team'].name}")
                    print(f"Builder has {len(builder_config['agents'])} agents")
                    print(f"Running builder with CREATE_FACTORY_TASK...")
                
                # Run builder team to create factory team
                result = app.run_team(
                    team=builder_config['team'],
                    task=CREATE_FACTORY_TASK,
                    agents=builder_config['agents'],
                    save_result=False  # Don't save output.json in team folder
                )
                
                # Validate generated files (should have agents.json and team.json)
                validation = app.validate_team_files(str(team_output_dir))
                
                success = validation["valid"] and len(validation["errors"]) == 0
                
                if success:
                    print(f"\n✓ Population member {i} created successfully")
                    if args.verbose:
                        print(f"  - agents.json: ✓")
                        print(f"  - team.json: ✓")
                else:
                    print(f"\n⚠ Population member {i} created with warnings:")
                    for error in validation["errors"]:
                        print(f"  ERROR: {error}")
                    for warning in validation["warnings"]:
                        print(f"  WARNING: {warning}")
                
                # Record metadata
                metadata["populations"].append({
                    "index": i,
                    "directory": str(pop_dir),
                    "team_directory": str(team_output_dir),
                    "success": success,
                    "validation": validation,
                    "rounds": result.get("rounds")
                })
                
            except Exception as e:
                print(f"\n✗ Failed to create population member {i}: {e}")
                
                if args.verbose:
                    import traceback
                    traceback.print_exc()
                
                metadata["populations"].append({
                    "index": i,
                    "directory": str(pop_dir),
                    "success": False,
                    "error": str(e)
                })
        
        # Save metadata
        metadata_path = output_dir / "population_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"POPULATION SETUP COMPLETE")
        print(f"{'='*60}")
        
        successful = sum(1 for p in metadata["populations"] if p.get("success", False))
        print(f"Successfully created: {successful}/{args.population_size}")
        print(f"Failed: {args.population_size - successful}/{args.population_size}")
        print(f"\nMetadata saved to: {metadata_path}")
        print(f"\nNote: Teams use predefined tools (no tools.json needed)")
        
        if successful < args.population_size:
            print(f"\n⚠ Warning: Not all population members were created successfully")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())