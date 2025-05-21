# Overview

This project merges what used to be a wrapper lib (tsAPI) supporting the TradeStation API and the almost blank project (tsClient) that will access said api. Unlike a conventional python project, we are not preparing to distribute a package. This is internal use only, hence, our first objective is to adjust the 2 src sets to recognize this new perspective.

I would question  the use of the folder named 'client' in the tsAPI folder. Let's update that to 'API'.

2nd Objective is to refactor the logging and exception handling in both to employ the same pattern in each. Be concise with messages in both subsystems.

Final objective for this iteration is to produce a login flow that leads to listing out the account details.

TASK TARGET:
Confine your review to code related to the interactions between client and api. At this stage we can tolerate some code smells in favor to quickly spinning up the basics of authentication and acct retrieval ops.

TASKS:

Review the code to refactor the client to lib relationship in those areas where we gain benefit (in terms of simplicity).
Update the code accordingly based on best practices of the python community.
Ensure that actions on both sides (client v lib) are robustly error handled and logged.  
Log messages should employ the same strings ae the error conditions that are detected.
In this iteration log msgs should document both input and outputs of given messages. Both caller and callee.
Output logs to csv format in the 'logs' folder where the filename indicates the given date in month-day format (05-21). The year is not needed.
Prefix log msgs with 'caller: ' or 'callee:'

RESOURCES:

https://api.tradestation.com/docs/specification/ We'll be using the V3 api. The OpenAPI spec is stored in the root of this project.
