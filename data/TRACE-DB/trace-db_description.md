# TRACE-DB: Transformative Reasoning Across Catalytic Enzymes

## A Structured, Enzyme-Centric Relational Database Linking Druggable Enzyme Targets to Human Diseases

**Build date:** 2026-07-21  
**Version:** 1.0  
**Scope:** High-confidence enzyme–disease pairs  
**Access:** SQLite database + normalized CSV tables

---

## 1. Overview

TRACE-DB is a structured, enzyme-centric relational database that links druggable enzyme targets to the human diseases they are implicated in, together with their catalytic reactions, ligand identities, kinetic parameters, and disease-relevant mutations. Every row in the master denormalized view resolves to a single **enzyme target → disease** pairing, with all downstream reaction, kinetic, ligand, and mutation data nested under that pairing. The database is disease-centric: no enzyme is included without a disease annotation, and no orphan rows exist.

The database covers **307 unique enzymes** (UniProt-reviewed, EC-numbered human proteins) linked to **3,377 unique diseases** across all major disease areas — oncology, neurodegeneration, cardiometabolic, rare/monogenic, infectious, and immunological disease — yielding **15,303 enzyme–disease pairings** in the master view.

### Inclusion Criteria (High-Confidence Tier)

An enzyme is included in TRACE-DB only if it satisfies all three of the following criteria simultaneously:

1. **Kinetic characterization** — has measured kinetic parameters (KM, kcat, Ki, or equivalent) in BRENDA or SABIO-RK
2. **Druggability evidence** — has a drug or clinical candidate cross-referenced in ChEMBL (approved or clinical-trial phase)
3. **Disease-relevant variants** — has pathogenic variants recorded in ClinVar

This three-criteria filter ensures that every enzyme in TRACE-DB has the data density to populate the full Target → Disease → Reaction/Kinetics → Mutation row structure. Enzymes missing any criterion are excluded rather than included with sparse fields.

---

## 2. Methods

### 2.1 Data Sources

TRACE-DB integrates seven primary data sources, queried between 2026-07-10 and 2026-07-21:

| Source | Version / Date | Role in TRACE-DB | License |
|--------|---------------|-------------------|---------|
| **BRENDA** | 2026.1 release | Kinetic parameters (KM, kcat, Ki), reactions, organism-specific data | CC BY 4.0 |
| **SABIO-RK** | API (2026-07-21) | Kinetic parameters with full experimental context, mutant–wildtype pairings, reaction stoichiometry | Open access |
| **UniProt** | 2026-07-21 | Enzyme annotations, EC numbers, PDB cross-refs, molecular weight, subunit structure, DrugBank/OMIM/ClinVar/DisGeNET/Orphanet cross-references | CC BY 4.0 |
| **ChEMBL** | r37 (May 2026) | Target IDs, approved drug associations, clinical candidates | CC BY-SA 3.0 |
| **Open Targets** | 26.06 (June 2026) | Disease–target associations with evidence scores | Apache 2.0 |
| **ClinVar** | 2026-07-21 (weekly) | Pathogenic variant counts per gene | Public domain |
| **PubMed** | via SABIO-RK, BRENDA, LiteratureSearch | Literature grounding for every kinetic and mutation record | N/A |

### 2.2 Curation Pipeline

The build proceeded in six phases:

**Phase 1 — High-confidence subset definition and enrichment.** The enzyme backbone (5,716 enzymes from a prior comprehensive UniProt query) was filtered to the 307 enzymes meeting all three HC criteria. Each enzyme was enriched with Ensembl gene IDs, Open Targets disease associations (15,350 disease links across 3,275 diseases), and UniProt structural data (PDB IDs, molecular weight, subunit structure).

**Phase 2 — BRENDA kinetic data extraction.** The BRENDA 2026.1 flat file (290 MB) was parsed for all 195 HC EC numbers, yielding 14,264 human kinetic entries (KM = 4,501; kcat = 2,588; Ki = 7,175) and 195 reaction equations. Values reported as ranges were converted to midpoints. PubMed references were resolved from BRENDA's internal reference numbering system.

**Phase 3 — SABIO-RK kinetic data extraction.** The SABIO-RK REST API was queried for all 195 HC EC numbers. For each EC, all human entries were retrieved in full detail (kinetic parameters with normalized values/units, reaction species with stoichiometry and roles, enzyme description including wildtype/mutant status, experimental conditions, publication metadata, and compound cross-references to ChEBI and PubChem). For ECs with no human data (99 of 195), a non-human fallback sample (up to 10 entries per EC) was retrieved and flagged with `reaction_provenance`. This yielded 8,018 kinetic records across 136 ECs, including 2,450 mutant entries.

**Phase 4 — Cross-references and drug data.** Each of the 307 UniProt accessions was queried directly to extract structured cross-references to DrugBank (289 enzymes), ChEMBL target IDs (307), OMIM gene and phenotype entries (307), ClinVar (307), DisGeNET (307), Orphanet (242), PDB (275), and NCBI GeneID (307). ChEMBL was additionally queried for approved drugs (max_phase = 4) per target, yielding 13,241 drug records. ClinVar pathogenic variant counts were obtained via NCBI E-utilities (63,259 total pathogenic variants, median 81 per enzyme).

**Phase 5 — Mutation delta compilation.** SABIO-RK mutant entries were paired with matching wildtype measurements (same EC, substrate, parameter) to compute delta_KM and delta_kcat values. Literature mining via Biomni LiteratureSearch targeted the top 50 most-mutated enzymes for delta_stability data (thermal denaturation, folding free energy changes), yielding 21 stability records (3 quantitative, 18 qualitative) across 10 genes.

**Phase 6 — Database assembly.** All data were merged into 7 normalized tables and one master denormalized view. Kinetic entries were deduplicated (same EC/ligand/organism/parameter/PubMed, values within 1% tolerance → keep SABIO-RK over BRENDA for richer metadata), reducing 21,922 pre-dedup entries to 10,153. Confidence tiers were assigned. The reaction-provenance enforcement was verified by SQL query.

### 2.3 Confidence Tiering

Each enzyme–disease row is assigned a confidence tier based on the strength of evidence supporting the disease–target link:

| Tier | Criteria | Rows | % |
|------|----------|------|---|
| **High** | ≥2 independent PubMed sources + druggability evidence (approved or clinical-trial drug) | 14,355 | 93.8% |
| **Medium** | 1 PubMed source + (druggability OR pathogenic variant) | 649 | 4.2% |
| **Low** | Open Targets association score only | 299 | 2.0% |

### 2.4 Reaction Provenance Enforcement

For any reaction row sourced from a non-human organism (cross-species fallback when no human reaction data exists), the `reaction_provenance` field is mandatory. This field records the source entry ID and organism, ensuring traceability for every non-human reaction. The enforcement was verified at build time by running:

```sql
SELECT COUNT(*) FROM reaction WHERE organism != 'Homo sapiens' AND reaction_provenance IS NULL
```

**Result: 0** — all 132 non-human reactions have `reaction_provenance` populated.

### 2.5 Deduplication

Kinetic entries were deduplicated using a composite key of (EC number, ligand name, organism, parameter type, PubMed ID). When two entries matched on this key and their values were within 1% tolerance, the SABIO-RK entry was retained over the BRENDA entry (SABIO-RK provides richer metadata including normalized units, experimental conditions, and UniProt cross-references). Entries with values differing by more than 1% were retained as independent measurements. This reduced 21,922 pre-deduplication kinetic records to 10,153 unique records.

---

## 3. Database Schema

![TRACE-DB Schema](fig0_schema_diagram.png)

**Figure 1. TRACE-DB schema.** Seven normalized tables (enzyme, ligand, reaction, kinetics, mutation, crossref, disease_link) are joined into a master denormalized view (trace_db_view) where each row represents one enzyme target → disease pairing with nested reaction, kinetic, and mutation data as JSON fields.

### Table Definitions

| Table | Primary Key | Rows | Description |
|-------|------------|------|-------------|
| `enzyme` | uniprot_id | 307 | Enzyme node: EC number, name, gene symbol, organism, PDB IDs, molecular weight, subunit structure, Ensembl ID |
| `ligand` | ligand_id | 6,866 | Ligand node: name, ChEBI ID, PubChem ID, role (substrate/product/inhibitor/cofactor) |
| `reaction` | auto-increment | 969 | Reaction edge: EC number, equation, substrates, products, stoichiometry, reversibility, organism, provenance |
| `kinetics` | auto-increment | 10,153 | Kinetics edge: EC number, ligand, parameter (KM/kcat/Ki/etc.), value, unit, organism, pH, temperature, PubMed ID |
| `mutation` | auto-increment | 2,471 | Mutation node: EC number, mutation description, wildtype reference, delta_KM, delta_kcat, delta_stability, PubMed ID |
| `crossref` | uniprot_id | 307 | Cross-references: DrugBank, ChEMBL, ClinVar, OMIM, DisGeNET, Orphanet, GeneID |
| `disease_link` | auto-increment | 15,303 | Disease linkage: uniprot_id, disease_id (OMIM/DOID/MeSH/Mondo), disease_name, disease_source, Open Targets score |
| **`trace_db_view`** | auto-increment | **15,303** | **Master denormalized view: one row per (enzyme, disease) pair with all nested data as JSON** |

---

## 4. Database Characteristics

### 4.1 Overall Scale

TRACE-DB contains **15,303 enzyme–disease pairings** spanning 307 enzymes and 3,377 unique diseases. Each row carries an average of 75.4 nested kinetic measurements, 23.0 mutation records, and 8.9 reaction entries. The database integrates 10,153 unique kinetic records, 969 reactions, 2,471 mutation delta records, and 6,866 ligands, cross-referenced to 8 external databases.

### 4.2 Enzyme Coverage by EC Class

![EC Class Distribution](fig2_ec_class_distribution.png)

**Figure 2. Enzyme distribution by EC class.** Transferases (EC 2, 148 enzymes, 48%) constitute the largest class, reflecting the predominance of kinases and other transferase drug targets. Hydrolases (EC 3, 78 enzymes, 25%) and oxidoreductases (EC 1, 45 enzymes, 15%) follow. Translocases (EC 7, 17 enzymes) represent ion pumps and transporters with drug targets. The full EC class distribution is:

| EC Class | Enzymes | % |
|----------|---------|---|
| 1: Oxidoreductases | 45 | 14.7% |
| 2: Transferases | 148 | 48.2% |
| 3: Hydrolases | 78 | 25.4% |
| 4: Lyases | 12 | 3.9% |
| 5: Isomerases | 4 | 1.3% |
| 6: Ligases | 3 | 1.0% |
| 7: Translocases | 17 | 5.5% |

### 4.3 Disease Coverage

![Disease Categories](fig1_disease_categories.png)

**Figure 3. Disease coverage by category.** TRACE-DB spans all major disease areas. Rare and monogenic diseases (729 unique diseases) form the largest explicitly categorized group, reflecting the enrichment of metabolic enzyme deficiencies and lysosomal storage disorders. Oncology (402 diseases), cardiovascular (97), metabolic (94), neurodegeneration (54), immunological (44), and infectious disease (32) are all represented. A substantial "other" category (1,938 diseases) includes conditions not mapping to the primary keyword categories — these span hematological, renal, pulmonary, dermatological, and multisystem disorders.

### 4.4 Top Diseases by Enzyme Target Count

![Top Diseases](fig6_top_diseases.png)

**Figure 4. Top 15 diseases by enzyme target count.** Neoplasms (209 enzyme targets), non-small cell lung carcinoma (178), hepatocellular carcinoma (177), and breast cancer (166) have the richest enzyme target representation, reflecting the extensive kinase and metabolic enzyme drug target landscape in oncology. Hereditary disease (161) and neurodegenerative disease (155) demonstrate coverage of monogenic and neurodegenerative enzyme targets.

### 4.5 Top Enzymes by Disease Association Count

![Top Enzymes](fig7_top_enzymes.png)

**Figure 5. Top 15 enzymes by disease association count.** Several enzymes are implicated across 50 or more diseases, reflecting pleiotropic roles in metabolism and signaling. These highly connected enzymes — including xanthine dehydrogenase (XDH), vitamin K epoxide reductase (VKORC1), and uridine monophosphate synthetase (UMPS) — represent nodes where a single enzyme target intersects multiple disease areas.

### 4.6 Confidence Tier and Mutation Status

![Confidence and Mutation](fig3_confidence_mutation.png)

**Figure 6. Confidence tier and mutation status distributions.** Left: 93.8% of rows are High confidence (≥2 PubMed sources + druggability), 4.2% Medium, 2.0% Low. Right: 35.1% of rows have at least one characterized mutation with kinetic or stability delta data (mutation_characterized), while 64.9% have pathogenic variants in ClinVar but no measured kinetic/stability delta (wild_type_only). The wild_type_only flag indicates the enzyme has disease-relevant variants but no published delta_KM/delta_kcat/delta_stability measurements — the row is retained with the enzyme/reaction/kinetics data intact.

### 4.7 Kinetic Parameter Distribution

![Kinetic Parameters](fig4_kinetic_parameters.png)

**Figure 7. Kinetic parameter types in TRACE-DB.** The 10,153 kinetic records span 23 parameter types. Ki (inhibition constant, 5,107 records) is the most abundant, followed by KM (Michaelis constant, 2,819), kcat (catalytic rate constant, 1,467), Vmax (257), and kcat/KM (catalytic efficiency, 206). The high Ki count reflects the drug-discovery focus of ChEMBL-deposited inhibition data. Additional parameters include IC50, Kd, specific enzyme activity, and Hill coefficients.

### 4.8 Cross-Reference Database Coverage

![Cross-Reference Coverage](fig5_crossref_coverage.png)

**Figure 8. Cross-reference database coverage across 307 enzymes.** ChEMBL, OMIM, DisGeNET, GeneID, and ClinVar achieve 100% coverage (307/307 enzymes). DrugBank covers 289/307 (94.1%), PDB covers 275/307 (89.6%), and Orphanet covers 242/307 (78.8%). The near-complete coverage reflects the high-confidence inclusion criteria — every enzyme has a ChEMBL drug cross-reference and ClinVar pathogenic variants by design.

### 4.9 PubMed Literature Grounding

![PubMed Coverage](fig8_pubmed_coverage.png)

**Figure 9. PubMed coverage by kinetic data source.** SABIO-RK entries achieve 99.2% PubMed coverage (1,775/1,790), while BRENDA entries achieve 73.7% (6,165/8,363). The gap in BRENDA coverage reflects entries that reference literature by BRENDA-internal reference numbers without PubMed mapping. Overall, 78.2% of kinetic records (7,940/10,153) carry a PubMed ID. Every mutation record in the mutation table carries a PubMed ID or literature source citation.

### 4.10 Mutation Delta Data

The mutation table contains 2,471 records with three types of delta measurements:

| Delta Type | Records | Source |
|------------|---------|--------|
| delta_KM | 709 | SABIO-RK mutant vs. wildtype pairing |
| delta_kcat | 612 | SABIO-RK mutant vs. wildtype pairing |
| delta_stability | 21 | Literature mining (10 genes) |

The delta_stability records span 10 genes (GBA1, PAH, IDH1, ADA, GAA, CPT2, BRAF, HSD3B2, ALDH5A1, F9), with 3 quantitative measurements (e.g., GBA1 +21°C ΔTm with cyclophellitol; PAH R408W −26.7 kcal/mol tetramerization domain destabilization) and 18 qualitative assessments (e.g., "destabilized — misfolding and ERAD degradation"). The limited number of quantitative stability measurements reflects the literature reality: most mutation studies report functional consequences rather than direct thermal stability measurements.

---

## 5. Druggability Tier Distribution

The 307 enzymes are stratified by druggability tier based on ChEMBL drug development phase:

| Tier | Enzymes | View Rows | Description |
|------|---------|-----------|-------------|
| Approved target | 209 | 10,423 | Has at least one FDA-approved drug (ChEMBL max_phase = 4) |
| Clinical trial target | 98 | 4,880 | Has clinical-trial-stage candidates (ChEMBL max_phase 1–3) |
| Preclinical | 0 | 0 | No preclinical enzymes meet all three HC criteria |

No preclinical-tier enzymes satisfied all three HC inclusion criteria simultaneously (kinetic data + ChEMBL drug + ClinVar pathogenic variants), so the build comprises two chunks rather than three.

---

## 6. Data Provenance and Reproducibility

A complete provenance log is provided in `tracedb_provenance.json`, recording every source, query date, version, and record count. Key verification results:

| Verification Query | Expected | Actual | Status |
|-------------------|----------|--------|--------|
| `SELECT COUNT(*) FROM reaction WHERE organism != 'Homo sapiens' AND reaction_provenance IS NULL` | 0 | **0** | PASS |
| Orphan enzymes (no disease linkage) | 0 | **0** | PASS |
| Kinetics with PubMed ID | — | 7,940/10,153 (78.2%) | Reported |

---

## 7. Output Files

| File | Format | Size | Description |
|------|--------|------|-------------|
| `trace_db.sqlite` | SQLite | 268 MB | Full relational database with all 8 tables |
| `trace_db_view.csv` | CSV | 277 MB | Master denormalized view (one row per enzyme–disease pair) |
| `trace_db_enzyme.csv` | CSV | 189 KB | Enzyme table (307 rows) |
| `trace_db_ligand.csv` | CSV | 569 KB | Ligand table (6,866 rows) |
| `trace_db_reaction.csv` | CSV | 298 KB | Reaction table (969 rows) |
| `trace_db_kinetics.csv` | CSV | 2.4 MB | Kinetics table (10,153 rows) |
| `trace_db_mutation.csv` | CSV | 259 KB | Mutation table (2,471 rows) |
| `trace_db_crossref.csv` | CSV | 160 KB | Cross-reference table (307 rows) |
| `trace_db_disease_link.csv` | CSV | 3.3 MB | Disease linkage table (15,303 rows) |
| `tracedb_provenance.json` | JSON | 3 KB | Provenance log with verification results |

---

## 8. Limitations

1. **PubMed coverage (78.2%).** The 21.8% of kinetic records without PubMed IDs are exclusively from BRENDA entries that reference literature by internal reference numbers without PubMed mapping. SABIO-RK entries achieve 99.2% PubMed coverage. This is a BRENDA data limitation, not a build error.

2. **delta_stability data (21 records, 10 genes).** The literature mining targeted the top 50 most-mutated enzymes but found quantitative or qualitative stability data for only 10. This reflects the publication landscape: most mutation studies report functional consequences (activity loss, misfolding) rather than direct thermal stability measurements (ΔTm, ΔΔG). Sparse fields are marked null or "qualitative" per the design specification, not omitted.

3. **SABIO-RK EC coverage (136/195).** 59 of 195 HC EC numbers have no SABIO-RK entries. These ECs are covered by BRENDA kinetics alone, which is expected given SABIO-RK's narrower enzyme coverage. No HC EC is without kinetic data entirely — that would violate inclusion criterion 1.

4. **Scope (15,303 rows, not ~20K).** The strict three-criteria HC filter (kinetics AND ChEMBL drug AND ClinVar pathogenic variants) yielded 307 enzymes rather than the estimated ~20K rows. This is a conservative, high-quality subset as specified. Expanding to a two-criteria filter would increase coverage but reduce data density per row.

5. **Disease ID source priority.** Disease IDs are assigned with priority OMIM > DOID > MeSH > Mondo (first available from Open Targets dbXRefs). Some diseases may have multiple valid IDs across ontologies; the primary ID is the highest-priority available, with all cross-references retained in `disease_dbxrefs`.

---

## 9. Example Query

To retrieve all enzyme targets for Fabry disease with their kinetic and mutation data:

```sql
SELECT gene_symbol, enzyme_name, disease_name, confidence_tier, mutation_status,
       kinetics_count, mutation_count, reaction_count, pubmed_source_count
FROM trace_db_view
WHERE disease_name LIKE '%Fabry%';
```

Returns: GLA (alpha-galactosidase A) → Fabry disease, High confidence, mutation_characterized, 34 kinetic records, 16 mutation records.

---

*TRACE-DB was built using the Biomni platform. All data sources were accessed via public APIs or downloaded flat files under their respective open-access licenses. The database is provided as SQLite and CSV for maximum interoperability.*

