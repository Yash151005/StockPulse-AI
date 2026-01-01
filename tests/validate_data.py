"""
StockPulse AI - Data Validation Script
=======================================
Validates stock data quality and identifies issues
"""

import pandas as pd
from datetime import datetime

def validate_daily_stock_data(df: pd.DataFrame) -> dict:
    """
    Comprehensive validation of daily stock data
    
    Args:
        df: DataFrame with daily stock records
        
    Returns:
        Dictionary with validation results and issues
    """
    
    issues = []
    warnings = []
    metrics = {}
    
    # 1. Check for required columns
    required_columns = [
        'record_date', 'location_code', 'item_code', 
        'opening_stock', 'receipts', 'issues', 'closing_stock'
    ]
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        issues.append(f"Missing required columns: {missing_columns}")
        return {
            'is_valid': False,
            'issues': issues,
            'warnings': [],
            'metrics': {}
        }
    
    # 2. Check for negative stock values
    negative_stock = df[df['closing_stock'] < 0]
    if len(negative_stock) > 0:
        issues.append(f"Found {len(negative_stock)} records with negative closing stock")
        metrics['negative_stock_count'] = len(negative_stock)
    
    # 3. Check for stock balance equation
    df['calculated_closing'] = df['opening_stock'] + df['receipts'] - df['issues']
    df['balance_difference'] = abs(df['closing_stock'] - df['calculated_closing'])
    
    mismatches = df[df['balance_difference'] > 0.01]
    if len(mismatches) > 0:
        issues.append(f"Found {len(mismatches)} records with stock balance mismatches")
        metrics['balance_mismatch_count'] = len(mismatches)
        metrics['max_balance_difference'] = df['balance_difference'].max()
    
    # 4. Check for future dates
    today = datetime.now().date()
    df['record_date'] = pd.to_datetime(df['record_date']).dt.date
    future_dates = df[df['record_date'] > today]
    
    if len(future_dates) > 0:
        issues.append(f"Found {len(future_dates)} records with future dates")
        metrics['future_date_count'] = len(future_dates)
    
    # 5. Check for missing critical fields
    missing_location = df[df['location_code'].isna() | (df['location_code'] == '')]
    if len(missing_location) > 0:
        warnings.append(f"Found {len(missing_location)} records with missing location_code")
    
    missing_item = df[df['item_code'].isna() | (df['item_code'] == '')]
    if len(missing_item) > 0:
        warnings.append(f"Found {len(missing_item)} records with missing item_code")
    
    # 6. Check for duplicate records
    duplicates = df[df.duplicated(subset=['record_date', 'location_code', 'item_code'], keep=False)]
    if len(duplicates) > 0:
        issues.append(f"Found {len(duplicates)} duplicate records (same date, location, item)")
        metrics['duplicate_count'] = len(duplicates)
    
    # 7. Check date continuity
    for location in df['location_code'].unique():
        for item in df['item_code'].unique():
            loc_item_df = df[(df['location_code'] == location) & (df['item_code'] == item)].sort_values('record_date')
            
            if len(loc_item_df) > 1:
                date_diffs = loc_item_df['record_date'].diff().dt.days
                gaps = date_diffs[date_diffs > 1]
                
                if len(gaps) > 0:
                    warnings.append(f"Date gaps found for {location}/{item}: {len(gaps)} gaps")
    
    # 8. Data completeness metrics
    metrics['total_records'] = len(df)
    metrics['unique_locations'] = df['location_code'].nunique()
    metrics['unique_items'] = df['item_code'].nunique()
    metrics['date_range_start'] = df['record_date'].min()
    metrics['date_range_end'] = df['record_date'].max()
    metrics['days_covered'] = (df['record_date'].max() - df['record_date'].min()).days
    
    # 9. Null value checks
    for col in ['opening_stock', 'receipts', 'issues', 'closing_stock']:
        null_count = df[col].isna().sum()
        if null_count > 0:
            warnings.append(f"Column '{col}' has {null_count} null values")
    
    # 10. Value range checks
    if df['opening_stock'].max() > 1_000_000:
        warnings.append("Some opening_stock values exceed 1M units - verify correctness")
    
    if df['issues'].max() > 10_000:
        warnings.append("Some daily issues exceed 10K units - verify correctness")
    
    # Final validation status
    is_valid = len(issues) == 0
    
    return {
        'is_valid': is_valid,
        'issues': issues,
        'warnings': warnings,
        'metrics': metrics,
        'validation_timestamp': datetime.now().isoformat()
    }


def generate_validation_report(validation_results: dict) -> str:
    """
    Generate a human-readable validation report
    
    Args:
        validation_results: Output from validate_daily_stock_data
        
    Returns:
        Formatted report string
    """
    
    report = []
    report.append("=" * 80)
    report.append("STOCKPULSE AI - DATA VALIDATION REPORT")
    report.append("=" * 80)
    report.append(f"Validation Timestamp: {validation_results['validation_timestamp']}")
    report.append("")
    
    # Overall Status
    if validation_results['is_valid']:
        report.append("✅ VALIDATION PASSED - No critical issues found")
    else:
        report.append("❌ VALIDATION FAILED - Critical issues detected")
    
    report.append("")
    report.append("-" * 80)
    
    # Metrics
    if validation_results['metrics']:
        report.append("DATA METRICS:")
        report.append("-" * 80)
        for key, value in validation_results['metrics'].items():
            report.append(f"  {key}: {value}")
        report.append("")
    
    # Issues
    if validation_results['issues']:
        report.append("CRITICAL ISSUES:")
        report.append("-" * 80)
        for i, issue in enumerate(validation_results['issues'], 1):
            report.append(f"  {i}. ❌ {issue}")
        report.append("")
    else:
        report.append("✅ No critical issues found")
        report.append("")
    
    # Warnings
    if validation_results['warnings']:
        report.append("WARNINGS:")
        report.append("-" * 80)
        for i, warning in enumerate(validation_results['warnings'], 1):
            report.append(f"  {i}. ⚠️  {warning}")
        report.append("")
    else:
        report.append("✅ No warnings")
        report.append("")
    
    report.append("=" * 80)
    
    return "\n".join(report)


def validate_master_data(locations_df: pd.DataFrame, items_df: pd.DataFrame) -> dict:
    """
    Validate master data (locations and items)
    
    Args:
        locations_df: LOCATION_MASTER data
        items_df: ITEM_MASTER data
        
    Returns:
        Validation results
    """
    
    issues = []
    warnings = []
    
    # Check locations
    if 'location_code' in locations_df.columns:
        duplicate_locations = locations_df[locations_df.duplicated('location_code', keep=False)]
        if len(duplicate_locations) > 0:
            issues.append(f"Found {len(duplicate_locations)} duplicate location codes")
        
        missing_location_names = locations_df[locations_df['location_name'].isna()]
        if len(missing_location_names) > 0:
            warnings.append(f"Found {len(missing_location_names)} locations with missing names")
    
    # Check items
    if 'item_code' in items_df.columns:
        duplicate_items = items_df[items_df.duplicated('item_code', keep=False)]
        if len(duplicate_items) > 0:
            issues.append(f"Found {len(duplicate_items)} duplicate item codes")
        
        missing_item_names = items_df[items_df['item_name'].isna()]
        if len(missing_item_names) > 0:
            warnings.append(f"Found {len(missing_item_names)} items with missing names")
        
        if 'default_lead_time_days' in items_df.columns:
            invalid_lead_times = items_df[
                (items_df['default_lead_time_days'] < 1) | 
                (items_df['default_lead_time_days'] > 90)
            ]
            if len(invalid_lead_times) > 0:
                warnings.append(f"Found {len(invalid_lead_times)} items with unusual lead times (< 1 or > 90 days)")
    
    return {
        'is_valid': len(issues) == 0,
        'issues': issues,
        'warnings': warnings,
        'location_count': len(locations_df),
        'item_count': len(items_df)
    }


# Example usage
if __name__ == "__main__":
    # This would be used with actual data
    # Example:
    # df = pd.read_csv('stock_data.csv')
    # results = validate_daily_stock_data(df)
    # print(generate_validation_report(results))
    
    print("Data validation module loaded successfully")
    print("Use validate_daily_stock_data(df) to validate your data")
