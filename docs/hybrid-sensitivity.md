# Wrong-hint sensitivity check

I registered this supplemental validation control before inspecting held-out predictions. I reuse exactly the six validation positions already used for the repair pilot. I change only the category in the structured hint. I supply IndexError for a WrongResult case and WrongResult for any exception case. I compare the resulting disabled-adapter base repair against both stored validation pilot responses. I run the same behavioral probes on all three repairs. These intentionally wrong hints measure sensitivity to the intervention. They are separate from observed classifier mistakes and do not change the frozen classifier or held-out architecture.

