# ts-py

Forked from [https://github.com/pattertj/ts-api]. Detached from the original repository to ease the development process.  

This lib functions as a wrapper around the API that's published by TradeStation (documented at: [https://github.com/tradestation/api-docs]) and will be used by client projects when creating trading apps. One such client project is: [https://github.com/justSteve/tsClient]

Longterm goal is to transition from original to adopt the conventions and patterns of [https://github.com/alexgolec/schwab-py]

## Development



1) Most pressing objective is to re-factor so was to permit the client app to return credentials without the lib needing to know what location those are stored in.
2) Review codebase and compare comments agaist method signatures. They don't always match. Create a list of problem areas but do not attempt to fix.
3) Create utility that parses the order string employed by Think Or Swim and create the equivalant for the TradeStation API.