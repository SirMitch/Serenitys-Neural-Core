tools OpenCode can call:
Tool						|	What it does
=======================================================================================
list_docs					|	Lists all 7 docs with size, section count, code block count
read_doc					|	Full doc text, optional max_chars truncation
get_toc						|	All headings with level + body preview — map a doc before reading
get_section					|	Fuzzy-matched section extraction by heading name
search						|	AND full-text across all docs, ±2 line context windows, optional doc filter
search_code					|	Code-block-only search — finds classes, constants, signatures fast
get_principles				|	Instant dump of all 10 Universal Design Principles
get_hard_limits				|	Instant dump of the full safety.py constants table
get_integration_contract	|	Module-to-module contract lookup (e.g. AC_02 → AC_01)