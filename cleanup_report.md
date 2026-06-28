# Repository Cleanup Report

This report catalogs all identified dead code, unused services, unused imports, commented-out code, and outstanding TODOs in the Andhra Pradesh AI-Powered Grievance Redressal System repository.

---

## 1. Dead Code & Unused Services

The following modules were verified as completely unused and disconnected from all active API entrypoints and UI routes.

* **`app/services/classification_service.py`**
  * *Reason*: The system's classification task is now handled entirely by the LangGraph `analyze` node using the `UnderstandingChain`.
  * *Affected Files*: None.
  * *Cleanup Action*: Propose deletion.
* **`app/services/routing_service.py`**
  * *Reason*: Department assignment and routing recommendations are handled by the LangGraph workflow using `UnderstandingChain`.
  * *Affected Files*: None.
  * *Cleanup Action*: Propose deletion.
* **`app/services/summary_service.py`**
  * *Reason*: Summaries are generated as part of the unified classification and parsing chain inside `UnderstandingChain`.
  * *Affected Files*: None.
  * *Cleanup Action*: Propose deletion.
* **`app/workflows/langchain_workflow.py`**
  * *Reason*: This is a backup workflow using sequential LangChain calls. The system has migrated to the state-machine orchestration model defined in `langgraph_workflow.py`. No references exist in `gradio_app.py` or the FastAPI route handlers.
  * *Affected Files*: None.
  * *Cleanup Action*: Propose deletion.

---

## 2. Unused Imports

The following imports are declared in active files but are never referenced.

| File Path | Unused Import Name | Line Number | Action Required |
| :--- | :--- | :--- | :--- |
| [app/api/routes/addresser.py](file:///c:/Users/naray/DATASCIENCE/PGRS/sabudh-pgrs-chatbot/app/api/routes/addresser.py) | `UploadFile` | 5 | Remove from `fastapi` imports |
| [app/api/routes/addresser.py](file:///c:/Users/naray/DATASCIENCE/PGRS/sabudh-pgrs-chatbot/app/api/routes/addresser.py) | `File` | 5 | Remove from `fastapi` imports |
| [app/api/routes/addresser.py](file:///c:/Users/naray/DATASCIENCE/PGRS/sabudh-pgrs-chatbot/app/api/routes/addresser.py) | `List` | 6 | Remove from `typing` imports |
| [app/api/routes/grievance.py](file:///c:/Users/naray/DATASCIENCE/PGRS/sabudh-pgrs-chatbot/app/api/routes/grievance.py) | `datetime` | 7 | Remove import statement |
| [app/services/audio_service.py](file:///c:/Users/naray/DATASCIENCE/PGRS/sabudh-pgrs-chatbot/app/services/audio_service.py) | `Optional` | 3 | Remove from `typing` imports |
| [app/services/llm_service.py](file:///c:/Users/naray/DATASCIENCE/PGRS/sabudh-pgrs-chatbot/app/services/llm_service.py) | `Optional` | 4 | Remove from `typing` imports |
| [app/workflows/langgraph_workflow.py](file:///c:/Users/naray/DATASCIENCE/PGRS/sabudh-pgrs-chatbot/app/workflows/langgraph_workflow.py) | `Priority` | 17 | Remove from `app.models.schemas` imports |
| [gradio_app.py](file:///c:/Users/naray/DATASCIENCE/PGRS/sabudh-pgrs-chatbot/gradio_app.py) | `datetime` | 9 | Remove import statement |
| [gradio_app.py](file:///c:/Users/naray/DATASCIENCE/PGRS/sabudh-pgrs-chatbot/gradio_app.py) | `Optional` | 10 | Remove from `typing` imports |
| [gradio_app.py](file:///c:/Users/naray/DATASCIENCE/PGRS/sabudh-pgrs-chatbot/gradio_app.py) | `Image` | 11 | Remove from `PIL` imports |
| [gradio_app.py](file:///c:/Users/naray/DATASCIENCE/PGRS/sabudh-pgrs-chatbot/gradio_app.py) | `BytesIO` | 12 | Remove from `io` imports |
| [gradio_app.py](file:///c:/Users/naray/DATASCIENCE/PGRS/sabudh-pgrs-chatbot/gradio_app.py) | `os` | 13 | Remove import statement |

*(Note: Imports in package level `__init__.py` files that are mapped inside `__all__` list are omitted from this list as they are exposed exports).*

---

## 3. Duplicate Models & Schemas

No exact duplicate model classes exist. However, minor schema structural discrepancies exist:
* **Addresser Update representation**: `AddresserUpdate` is located in `app/models/user.py` as the API body schema, whereas `AddresserUpdateRecord` is inside `app/models/schemas.py` to represent the subdocument saved in MongoDB.
* **Grievance Operations schemas**: Schemas like `UpdateGrievanceStatus` and `AssignGrievance` are defined in `app/models/user.py` rather than `app/models/schemas.py`.
* *Cleanup Action*: Keep them as they are to avoid API breaking changes, but document this schema organization split.

---

## 4. Unreachable LangGraph Nodes

An audit of `langgraph_workflow.py` confirms that the graph flow is fully linear and connected:
* **Node Order**: `analyze` → `suggest_redressal` → `save_to_db` → `END`.
* **Reachability**: 100% reachable. No orphan nodes exist.

---

## 5. Commented-out Code & Outstanding TODOs

### Commented-out Code
* **`app/models/user.py`**:
  * Line 69: `# grievances_handled: List[str] = []  # TODO: For addressers`

### Outstanding TODOs
* **`app/api/routes/addresser.py`**:
  * Line 297: `# TODO: Send notification to admin`
* **`app/api/routes/admin.py`**:
  * Line 120: `# TODO: Send notification to addressers in that department`
* **`app/models/user.py`**:
  * Line 69: `# TODO: For addressers`
* **`app/workflows/langchain_workflow.py`** (Unused backup file):
  * Line 579: `# TODO: Integrate with app.services.audio_service`
  * Line 589: `# TODO: Integrate with app.services.image_service`
  * Line 598: `# TODO: Integrate with app.services.document_service`
