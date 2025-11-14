import sys
import os
sys.path.append(os.path.abspath(".."))

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

from agent_evo.loaders.json_loader import JSONLoader
from agent_evo.llm.client import OpenAIClient

MERGE_PROMPT = """# TOOL CALLING AGENT
You are an expert AI agent that uses provided tools to complete assigned tasks.

# TOOL CALLING
When you need to use a tool, use the following structured syntax:

BEGIN_TOOL_CALL <tool_name>
BEGIN_ARG <argument_name>
<argument_value>
END_ARG
END_TOOL_CALL

For example:
BEGIN_TOOL_CALL calculate
BEGIN_ARG expression
2 + 2
END_ARG
END_TOOL_CALL

BEGIN_TOOL_CALL search
BEGIN_ARG query
AI news
END_ARG
BEGIN_ARG limit
5
END_ARG
END_TOOL_CALL

For multi-line arguments (like file content), you can use multiple lines:
BEGIN_TOOL_CALL file_writer
BEGIN_ARG path
output.txt
END_ARG
BEGIN_ARG content
Line 1 of content
Line 2 of content
Line 3 of content
END_ARG
END_TOOL_CALL

# Task
You are an expert AI team architect tasked with merging and improving two existing AI agent teams into a single, superior team.

=== TEAM 1 ===

**Tools (tools.json):**
{team1_tools}

**Agents (agents.json):**
{team1_agents}

**Team Structure (team.json):**
{team1_team}

=== TEAM 2 ===

**Tools (tools.json):**
{team2_tools}

**Agents (agents.json):**
{team2_agents}

**Team Structure (team.json):**
{team2_team}

=== YOUR TASK ===

Analyze both teams and create an improved, merged team that:

1. **Combines the best tools** from both teams
   - Remove duplicate tools (keep the better implementation)
   - Merge complementary tools
   - Improve tool implementations where possible
   - Ensure all tools have complete, working code

2. **Merges and improves agents**
   - Combine agents with similar roles into stronger specialists
   - Create new agents if needed to fill gaps
   - Improve system prompts to be more detailed and effective
   - Assign optimal tools to each agent
   - Set appropriate temperature and retry parameters

3. **Designs an improved team structure**
   - Borrow the best ideas from each team to make a better one
   - Create a logical delegation flow
   - Ensure efficient collaboration patterns
   - Set the best entry point agent
   - Avoid redundant edges while maintaining necessary connections

4. **Eliminates weaknesses**
   - Fix any issues in the original teams
   - Add missing capabilities
   - Improve error handling and robustness

=== OUTPUT REQUIREMENTS ===

You must create three files using the write_file tool:

1. **tools.json** - Combined and improved tools
2. **agents.json** - Merged and enhanced agents  
3. **team.json** - Optimized team structure

Format each file as valid JSON following the existing schemas.

=== GUIDELINES ===

**For Tools:**
- Each tool must have complete, executable Python code
- Include proper error handling
- Clear parameter descriptions
- No overlapping functionality

**For Agents:**
- System prompts should be 3-5 sentences minimum
- Clear role definitions and expertise areas
- Appropriate tool access (only what they need)
- Logical temperature settings (0.3-0.5 for analytical, 0.7-1.0 for creative)

**For Team:**
- Entry point should handle initial task analysis
- Delegation flow should be directed and logical
- Each edge should have a clear purpose
- Avoid cycles unless absolutely necessary

Begin by analyzing the strengths and weaknesses of each team, then create the improved merged team."""


def load_team_files(directory: Path) -> Dict[str, Any]:
    """Load all team files from a directory."""
    tools_path = directory / "tools.json"
    agents_path = directory / "agents.json"
    team_path = directory / "team.json"
    
    # Check all files exist
    missing = []
    if not tools_path.exists():
        missing.append("tools.json")
    if not agents_path.exists():
        missing.append("agents.json")
    if not team_path.exists():
        missing.append("team.json")
    
    if missing:
        raise FileNotFoundError(f"Missing files in {directory}: {', '.join(missing)}")
    
    # Load the files
    with open(tools_path, 'r') as f:
        tools = json.load(f)
    with open(agents_path, 'r') as f:
        agents = json.load(f)
    with open(team_path, 'r') as f:
        team = json.load(f)
    
    return {
        "tools": tools,
        "agents": agents,
        "team": team
    }


def merge_teams_with_llm(team1: Dict[str, Any], 
                         team2: Dict[str, Any],
                         llm_client: OpenAIClient,
                         output_dir: Path,
                         verbose: bool = False) -> Dict[str, Any]:
    """Use LLM to merge two teams into an improved version."""
    
    # Format the prompt
    prompt = MERGE_PROMPT.format(
        team1_tools=json.dumps(team1["tools"], indent=2),
        team1_agents=json.dumps(team1["agents"], indent=2),
        team1_team=json.dumps(team1["team"], indent=2),
        team2_tools=json.dumps(team2["tools"], indent=2),
        team2_agents=json.dumps(team2["agents"], indent=2),
        team2_team=json.dumps(team2["team"], indent=2)
    )
    
    # Create system prompt
    system_prompt = """You are an expert AI team architect. You have access to a write_file tool to create the merged team files.

Available tool:
- write_file(file_path: string, content: string): Write content to a file

Use the tool to create tools.json, agents.json, and team.json with the improved merged team."""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    
    print("\nSending merge request to LLM...")
    if verbose:
        print(f"\nPrompt length: {len(prompt)} characters")
    
    # Get LLM response
    response = llm_client.generate(
        messages=messages,
        temperature=0.7,
        max_tokens=8000
    )
    
    if verbose:
        print(f"\nLLM Response:\n{response}")
    
    # Parse tool calls from response
    from agent_evo.utils.parser import ToolCallParser
    from agent_evo.core.tool_executor import ToolExecutor
    from agent_evo.models.default_tools import create_file_writer_tool
    
    parser = ToolCallParser()
    executor = ToolExecutor()
    file_writer = create_file_writer_tool()
    
    _, tool_calls = parser.parse_response(response)
    
    if not tool_calls:
        print("\nWarning: LLM did not generate tool calls. Attempting to extract JSON directly...")
        # Try to extract JSON blocks from response
        import re
        
        # Look for JSON blocks for each file
        for filename in ["tools.json", "agents.json", "team.json"]:
            pattern = rf'```json.*?{filename}.*?\n(.*?)```'
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if not match:
                # Try without filename in header
                pattern = r'```json\s*\n(\{.*?\})\s*```'
                matches = re.findall(pattern, response, re.DOTALL)
                if matches:
                    # This is a fallback, might not work perfectly
                    print(f"Warning: Could not automatically extract {filename}")
            else:
                content = match.group(1).strip()
                output_path = output_dir / filename
                with open(output_path, 'w') as f:
                    f.write(content)
                print(f"Extracted {filename}")
    else:
        # Change to output directory before executing tools
        original_dir = os.getcwd()
        os.chdir(output_dir)
        
        try:
            # Execute tool calls
            print(f"\nExecuting {len(tool_calls)} tool calls...")
            for tool_call in tool_calls:
                if tool_call["tool"] == "write_file":
                    result = executor.execute_tool(file_writer, tool_call["arguments"])
                    if result["success"]:
                        print(f"✓ Created: {tool_call['arguments']['file_path']}")
                    else:
                        print(f"✗ Failed to create {tool_call['arguments']['file_path']}: {result['error']}")
        finally:
            os.chdir(original_dir)
    
    return {
        "response": response,
        "tool_calls": tool_calls
    }


def main():
    parser = argparse.ArgumentParser(
        description="Merge two AI agent teams into an improved combined team"
    )
    parser.add_argument(
        "--team1-dir", 
        required=True, 
        help="Directory containing first team's files (tools.json, agents.json, team.json)"
    )
    parser.add_argument(
        "--team2-dir",
        required=True,
        help="Directory containing second team's files (tools.json, agents.json, team.json)"
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory to save merged team files"
    )
    parser.add_argument(
        "--model",
        default="gpt-4o",
        help="LLM model to use for merging (default: gpt-4o)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    try:
        # Validate input directories
        team1_dir = Path(args.team1_dir)
        team2_dir = Path(args.team2_dir)
        
        if not team1_dir.exists():
            raise FileNotFoundError(f"Team 1 directory not found: {team1_dir}")
        if not team2_dir.exists():
            raise FileNotFoundError(f"Team 2 directory not found: {team2_dir}")
        
        print(f"Loading Team 1 from: {team1_dir}")
        team1 = load_team_files(team1_dir)
        print(f"✓ Loaded Team 1: {team1['team'].get('name', 'Unknown')}")
        
        print(f"\nLoading Team 2 from: {team2_dir}")
        team2 = load_team_files(team2_dir)
        print(f"✓ Loaded Team 2: {team2['team'].get('name', 'Unknown')}")
        
        # Create output directory
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"\nOutput directory: {output_dir.absolute()}")
        
        # Initialize LLM client
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("Missing OPENAI_API_KEY environment variable")
        
        llm_client = OpenAIClient(api_key=api_key, model=args.model)
        
        print("\n" + "="*60)
        print("MERGING TEAMS")
        print("="*60)
        
        # Merge teams
        result = merge_teams_with_llm(
            team1=team1,
            team2=team2,
            llm_client=llm_client,
            output_dir=output_dir,
            verbose=args.verbose
        )
        
        print("\n" + "="*60)
        print("MERGE COMPLETE")
        print("="*60)
        
        # Validate created files
        tools_path = output_dir / "tools.json"
        agents_path = output_dir / "agents.json"
        team_path = output_dir / "team.json"
        
        created_files = []
        if tools_path.exists():
            created_files.append("tools.json")
        if agents_path.exists():
            created_files.append("agents.json")
        if team_path.exists():
            created_files.append("team.json")
        
        if len(created_files) == 3:
            print("\n✓ All files created successfully:")
            print(f"  - tools.json")
            print(f"  - agents.json")
            print(f"  - team.json")
            
            # Validate JSON
            try:
                JSONLoader.load_tools(str(tools_path))
                print("\n✓ tools.json is valid")
            except Exception as e:
                print(f"\n⚠ tools.json validation warning: {e}")
            
            try:
                JSONLoader.load_agents(str(agents_path))
                print("✓ agents.json is valid")
            except Exception as e:
                print(f"⚠ agents.json validation warning: {e}")
            
            try:
                JSONLoader.load_team(str(team_path))
                print("✓ team.json is valid")
            except Exception as e:
                print(f"⚠ team.json validation warning: {e}")
        else:
            print(f"\n⚠ Warning: Only created {len(created_files)} of 3 files: {', '.join(created_files)}")
            print("You may need to manually extract the files from the LLM response.")
        
        # Save merge details
        merge_log_path = output_dir / "merge_log.json"
        with open(merge_log_path, 'w') as f:
            json.dump({
                "team1_dir": str(team1_dir),
                "team2_dir": str(team2_dir),
                "team1_name": team1['team'].get('name'),
                "team2_name": team2['team'].get('name'),
                "model": args.model,
                "llm_response": result["response"]
            }, f, indent=2)
        print(f"\nMerge log saved to: {merge_log_path}")
        
    except Exception as e:
        print(f"\nError: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()