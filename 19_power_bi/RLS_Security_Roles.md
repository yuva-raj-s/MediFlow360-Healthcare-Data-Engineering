# Row Level Security (RLS)
**Role**: `HospitalAdmin`
**DAX Filter**:
```dax
[hospital_code] = LOOKUPVALUE(
    user_hospital_mapping[hospital_code], 
    user_hospital_mapping[user_principal_name], 
    USERPRINCIPALNAME()
)
```
*Note*: This ensures the Madurai hospital director only sees Madurai data.