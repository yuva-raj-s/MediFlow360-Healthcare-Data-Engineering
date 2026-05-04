# LOG-004: HR Excel Merged Cells
**Severity**: P3 | **Status**: Open
**Author**: Priya Sharma (DE-001)

**What Happened**:
HR provides staff rosters via SharePoint Excel. The template has beautifully formatted merged header cells. ADF HTTP connector and PySpark Excel readers completely fail to parse merged cells cleanly.

**Struggle**:
We asked HR to provide a clean CSV. They refused, stating "the format is approved by management". 

**Current Workaround**:
We have a fragile pandas pre-processing script running locally that cleans the header before uploading. We are petitioning the CIO to mandate a standard export format.