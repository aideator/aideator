#!/usr/bin/env python3
"""Test script to verify formatter variant counting fix"""

from geneknow_pipeline.graph import run_pipeline
import json

# Create a simple test VCF file
test_vcf_content = """##fileformat=VCFv4.2
##contig=<ID=chr1>
##contig=<ID=chr2>
##INFO=<ID=GENE,Number=1,Type=String,Description="Gene name">
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	SAMPLE1
chr1	100	.	A	T	30	PASS	GENE=BRCA1	GT	0/1
chr1	200	.	G	C	40	PASS	GENE=BRCA2	GT	1/1
chr2	300	.	C	G	50	PASS	GENE=TP53	GT	0/1
chr2	400	.	T	A	60	PASS	GENE=KRAS	GT	0/1
chr2	500	.	G	A	70	PASS	GENE=EGFR	GT	1/1
"""

# Write test VCF
with open('test_variants.vcf', 'w') as f:
    f.write(test_vcf_content)

print("Running pipeline with test VCF containing 5 variants...")
try:
    # Run pipeline
    result = run_pipeline('test_variants.vcf')
    
    # Check the structured_json output
    if 'structured_json' in result:
        summary = result['structured_json'].get('summary', {})
        print('\n✅ Summary from structured_json:')
        print(f'  total_variants_found: {summary.get("total_variants_found", "NOT_FOUND")}')
        print(f'  variants_passed_qc: {summary.get("variants_passed_qc", "NOT_FOUND")}')
        print(f'  mutation_types: {summary.get("mutation_types", "NOT_FOUND")}')
    else:
        print('❌ No structured_json in result')
    
    # Also check raw state
    print('\n📊 Raw state data:')
    print(f'  filtered_variants length: {len(result.get("filtered_variants", []))}')
    print(f'  mutation_type_distribution: {result.get("mutation_type_distribution", "NOT_FOUND")}')
    print(f'  variant_count: {result.get("variant_count", "NOT_FOUND")}')
    
    # Verify the fix is working
    expected_count = 5
    actual_count = summary.get("total_variants_found", 0)
    
    if actual_count == expected_count:
        print(f'\n✅ SUCCESS: Formatter correctly reports {actual_count} variants!')
    else:
        print(f'\n❌ FAILURE: Expected {expected_count} variants but got {actual_count}')
        
except Exception as e:
    print(f"Error running pipeline: {e}")
    import traceback
    traceback.print_exc()
finally:
    # Clean up
    import os
    if os.path.exists('test_variants.vcf'):
        os.remove('test_variants.vcf')
        print("\nCleaned up test file")