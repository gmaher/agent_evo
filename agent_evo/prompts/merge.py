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

**Overall:**
- UNLEASH YOUR CREATIVITY, do not be afraid TO GO HAM. 
- You have access to a fully functional python environment and shell environment and may propose tools that fully utilize these.
- Propose both general purpose tools and specific tools tailored to each agent.
- Make the system prompts for the agents extensive and detailed.
- Feel free to create new tools and agents even if they aren't in the provided inputs

Begin by analyzing the strengths and weaknesses of each team, then create the improved merged team."""


MERGE_PROMPT_ONE_SHOT = """# TASK: MERGE AND IMPROVE TWO AI AGENT TEAMS

You are an expert AI team architect tasked with merging and improving two existing AI agent teams into a single, superior team.

=== TEAM 1 ===

**Agents (agents.json):**
{team1_agents}

**Team Structure (team.json):**
{team1_team}

=== TEAM 2 ===

**Agents (agents.json):**
{team2_agents}

**Team Structure (team.json):**
{team2_team}

=== YOUR TASK ===

Analyze both teams and create an improved, merged team that:

1. **Merges and improves agents**
   - Combine agents with similar roles into stronger specialists
   - Create new agents if needed to fill gaps
   - Improve system prompts to be more detailed and effective (5+ sentences)
   - Assign optimal tools to each agent
   - Set appropriate temperature and retry parameters

2. **Designs an improved team structure**
   - Borrow the best ideas from each team to make a better one
   - Create a logical delegation flow
   - Ensure efficient collaboration patterns
   - Set the best entry point agent
   - Avoid redundant edges while maintaining necessary connections

3. **Eliminates weaknesses**
   - Fix any issues in the original teams
   - Add missing capabilities
   - Improve error handling and robustness

=== OUTPUT REQUIREMENTS ===

You must output TWO JSON configurations in markdown code blocks:

1. **agents.json** - Merged and enhanced agents  
2. **team.json** - Optimized team structure

Format each as valid JSON following the schemas below.

=== GUIDELINES ===

**For Agents:**
- System prompts should be 5-10 sentences minimum with detailed expertise
- Clear role definitions and responsibilities
- Appropriate tool access (only what they need)
- Logical temperature settings (0.3-0.5 for analytical, 0.7-1.0 for creative)

**For Team:**
- Entry point should handle initial task analysis
- Delegation flow should be directed and logical
- Each edge should have a clear purpose
- Avoid cycles unless absolutely necessary

**Overall:**
- UNLEASH YOUR CREATIVITY - don't be afraid to GO BIG
- Create both general purpose and specialized tools
- Make system prompts extensive and detailed
- Feel free to create new agents even if they aren't in the provided inputs
- Focus on creating an extended team that's better than either input

=== JSON SCHEMAS ===

**agents.json Schema:**
{{
  "agents": [
    {{
      "id": "string (unique identifier)",
      "name": "string (agent display name)",
      "system_prompt": "string (detailed agent personality and instructions)",
      "tool_names": ["string (tool id)", ...],
      "temperature": number (0.0 to 1.0, default 0.7),
      "max_retries": number (optional, default 3)
    }}
  ]
}}

**team.json Schema:**
{{
  "id": "string (unique identifier)",
  "name": "string (team display name)",
  "description": "string (team purpose)",
  "agent_ids": ["string (agent id)", ...],
  "edges": [
    {{
      "from": "string (source agent id)",
      "to": "string (target agent id)",
      "description": "string (delegation purpose)"
    }}
  ],
  "entry_point": "string (starting agent id)"
}}

=== OUTPUT FORMAT ===

Output your response with both JSON configurations in markdown code blocks (make sure to include the filenames agents.json and team.json):

```json agents.json
{{ your merged agents configuration }}
```

```json team.json
{{ your merged team configuration }}
```
Do NOT include any other text or explanations. Output ONLY the two JSON code blocks."""