"""Compatibility exports for Meta Analysis workflow pages."""

from app.meta_analysis.pages.protocol_page import (
    ProtocolPage,
    ProtocolPageState,
    build_protocol_search_strategy_draft,
    execute_protocol_pubmed_search,
    initial_protocol_page_state,
    protocol_page_state_from_project,
    render_pubmed_search_execution_summary,
    render_search_strategy_summary,
    write_pubmed_search_execution_artifacts,
    write_protocol_search_strategy_artifacts,
)

__all__ = [
    "ProtocolPage",
    "ProtocolPageState",
    "build_protocol_search_strategy_draft",
    "execute_protocol_pubmed_search",
    "initial_protocol_page_state",
    "protocol_page_state_from_project",
    "render_pubmed_search_execution_summary",
    "render_search_strategy_summary",
    "write_pubmed_search_execution_artifacts",
    "write_protocol_search_strategy_artifacts",
]
