# VNet Architecture

- **Subnet 1 (Public)**: NA. No public facing web apps.
- **Subnet 2 (Private)**: Azure SQL Database and ADLS Gen2 configured with Service Endpoints.
- **On-Premise connection**: No Site-to-Site VPN (due to cost). We use ADF Self-Hosted Integration Runtime (SHIR) installed on a Windows VM inside the hospital firewall. It polls ADF for jobs using outbound HTTPS port 443.