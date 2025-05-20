This project merges what used to be a wrapper lib supporting the TradeStation API and my client that employed said api. Our first objective is to adjust the 2 src sets to recognize this new perspective on the current code base.

TASK TARGET:
Confine review to code related to the interactions between client and api. At this stage we can tolerate some code smells and even out right flaws in favor to quickly spinning up the basics of authentication and acct retrival ops.

TASKS:

Review the code to refactor the client to lib relationship in those areas where we gain benefit (in terms of simplicity). 
Update the code accoringly based on best practices of the python community.
Ensure that actions on both sides (client v lib) are robustly error handled and logged.  
Log messages should employ the same strings are the error conditions that are detected.
In this iteration log msgs should document both input and outputs of given messages. Both caller and callee. 
Prefix log msgs with 'caller: ' or 'callee: '
