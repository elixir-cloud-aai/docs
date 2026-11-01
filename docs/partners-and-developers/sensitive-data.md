# Sensitive Data

Sensitive human data, for example genetic and clinical data, is central to
biomedical research. Its use brings duties for data protection and privacy.
This page gives the background that partners and developers need to design an
integration for such data: the legal frameworks, the types of secure
environments and the four ways in which researchers can reach data. It is
background, not legal advice. Ask your data protection officer about your
case.

## Legal frameworks

Two EU frameworks govern the use of sensitive data in research:

- **GDPR** (General Data Protection Regulation) allows the use of sensitive
  personal data for research if safeguards are in place. The legal basis can
  differ, for example a task in the public interest or the informed consent
  of the data subjects. It depends on the research and on national law.
  Always minimise the data, pseudonymise it and control access. A Data
  Protection Impact Assessment (DPIA) is strongly recommended.
- **EHDS** (European Health Data Space) builds on GDPR. It sets one framework
  for sharing electronic health data across the EU and for its secondary use,
  for example in research, innovation and policymaking. See [Regulation (EU)
  2025/327][eur-lex-ehds]. Under the EHDS, health data may be reused if it is
  anonymised or pseudonymised and accessed in a Secure Processing
  Environment.

## Secure environments

Three terms describe places where sensitive data can be processed safely:

- **Trusted Execution Environment (TEE):** a protected area of a processor.
  It keeps code and data confidential and intact while they run.
- **Secure Processing Environment (SPE):** a controlled environment for
  processing and analysing data with confidentiality, integrity and privacy.
  The EHDS requires an SPE for the secondary use of health data.
- **Trusted Research Environment (TRE):** a controlled environment for
  research. It covers data access, analysis, collaboration, and legal and
  ethical compliance. The [Five Safes framework][ukdataservice-5-safes] is a
  common basis for TREs.

SPEs and TREs are very similar. The term SPE comes from the EHDS. The term
TRE originates in the UK.

All three aim to isolate their content from the platform they run on, to
protect the data against compromise, to check who may run code and access
data, and to let researchers analyse data and work together without moving
the data out. How well they do this depends on how an environment is built
and run. Before you rely on one, check its isolation and its controls for
data leaving the environment.

## Four ways to reach data

The ways in which researchers reach sensitive data depend on two questions:
is the data in one place or in many, and is it processed in the cloud or in
the researcher's own environment?

|                    | Local processing   | Cloud processing     |
| ------------------ | ------------------ | -------------------- |
| **Central data**   | Data repository    | Cloud platform       |
| **Federated data** | Federated database | Federated processing |

- **Data repository:** the data is in one database. Researchers request
  access. After approval, they download encrypted data to their own secure
  environment.
- **Federated database:** the data is spread over several nodes. A central
  portal and APIs expose its metadata. Researchers request access at the
  nodes that hold the data they need.
- **Cloud platform:** the data is on one platform. Authorised users log in
  and analyse it in an SPE, with workflows or interactive tools.
- **Federated processing:** the data stays on separate nodes, and its
  transfer is restricted (the nodes must enforce this). The analysis runs through APIs in an SPE and often combines results
  from several sources. Federated learning is a special case: a model is
  trained in several rounds with different datasets.

## Where to go next

- To try an analysis in an SPE, see [Researchers](../researchers/index.md).
- To plan access for your users and service, see [User Stories](user-stories.md).
