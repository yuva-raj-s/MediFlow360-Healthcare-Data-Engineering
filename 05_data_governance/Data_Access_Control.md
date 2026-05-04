# Data Access Control Matrix
## MediFlow360

Role-Based Access Control (RBAC) across the Azure environment.

| Role | Azure AD Group | ADLS Bronze | ADLS Silver | ADLS Gold | Azure SQL | Power BI |
|------|----------------|-------------|-------------|-----------|-----------|----------|
| Lead DE (DE-001) | `sg-mrhs-de-leads` | Read/Write | Read/Write | Read/Write | DBO | Admin |
| Data Engineer | `sg-mrhs-de-devs` | Read/Write | Read/Write | Read | Reader | Viewer |
| Data Analyst (DA-001)| `sg-mrhs-da` | None | Read | Read | Reader | Contributor |
| Stakeholders | `sg-mrhs-exec` | None | None | None | None | Viewer (RLS) |
| Service Principal | `sp-adf-mediflow360`| Read/Write | None | None | SP_Exec | None |
| Service Principal | `sp-dbx-mediflow360`| Read | Read/Write | Read/Write | SP_Exec | None |

**Notes**:
- ADF Service Principal writes to Bronze. Databricks reads Bronze, writes to Silver/Gold.
- Human users NEVER write to production ADLS directly. All writes happen via CI/CD pipelines.