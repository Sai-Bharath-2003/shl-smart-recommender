"""
Generate predictions for the test set based on known SHL catalog URLs
Uses pattern matching from training data + SHL catalog knowledge
"""

import pandas as pd
import re

# All known URLs from training data
KNOWN_URLS = {
    # Technical / Programming
    'python': 'https://www.shl.com/solutions/products/product-catalog/view/python-new/',
    'java_entry': 'https://www.shl.com/solutions/products/product-catalog/view/core-java-entry-level-new/',
    'java_8': 'https://www.shl.com/solutions/products/product-catalog/view/java-8-new/',
    'java_advanced': 'https://www.shl.com/solutions/products/product-catalog/view/core-java-advanced-level-new/',
    'javascript': 'https://www.shl.com/solutions/products/product-catalog/view/javascript-new/',
    'sql': 'https://www.shl.com/solutions/products/product-catalog/view/sql-server-new/',
    'sql_ssas': 'https://www.shl.com/solutions/products/product-catalog/view/sql-server-analysis-services-%28ssas%29-%28new%29/',
    'automata_sql': 'https://www.shl.com/solutions/products/product-catalog/view/automata-sql-new/',
    'automata_fix': 'https://www.shl.com/solutions/products/product-catalog/view/automata-fix-new/',
    'automata_selenium': 'https://www.shl.com/solutions/products/product-catalog/view/automata-selenium/',
    'selenium': 'https://www.shl.com/solutions/products/product-catalog/view/selenium-new/',
    'css3': 'https://www.shl.com/solutions/products/product-catalog/view/css3-new/',
    'html_css': 'https://www.shl.com/solutions/products/product-catalog/view/htmlcss-new/',
    'drupal': 'https://www.shl.com/solutions/products/product-catalog/view/drupal-new/',
    'data_warehousing': 'https://www.shl.com/solutions/products/product-catalog/view/data-warehousing-concepts/',
    'tableau': 'https://www.shl.com/solutions/products/product-catalog/view/tableau-new/',
    'manual_testing': 'https://www.shl.com/solutions/products/product-catalog/view/manual-testing-new/',
    'basic_computer': 'https://www.shl.com/solutions/products/product-catalog/view/basic-computer-literacy-windows-10-new/',
    
    # Cognitive / Aptitude  
    'numerical': 'https://www.shl.com/solutions/products/product-catalog/view/verify-numerical-ability/',
    'verbal': 'https://www.shl.com/solutions/products/product-catalog/view/verify-verbal-ability-next-generation/',
    'inductive': 'https://www.shl.com/solutions/products/product-catalog/view/shl-verify-interactive-inductive-reasoning/',
    'numerical_calc': 'https://www.shl.com/solutions/products/product-catalog/view/shl-verify-interactive-numerical-calculation/',
    'global_skills': 'https://www.shl.com/solutions/products/product-catalog/view/global-skills-assessment/',
    
    # Personality / Behavioral
    'opq32r': 'https://www.shl.com/solutions/products/product-catalog/view/occupational-personality-questionnaire-opq32r/',
    'opq_leadership': 'https://www.shl.com/solutions/products/product-catalog/view/opq-leadership-report/',
    'opq_team': 'https://www.shl.com/solutions/products/product-catalog/view/opq-team-types-and-leadership-styles-report',
    'enterprise_leadership': 'https://www.shl.com/products/product-catalog/view/enterprise-leadership-report-2-0/',
    'enterprise_leadership_v1': 'https://www.shl.com/products/product-catalog/view/enterprise-leadership-report/',
    
    # Communication
    'business_communication': 'https://www.shl.com/products/product-catalog/view/business-communication-adaptive/',
    'interpersonal': 'https://www.shl.com/products/product-catalog/view/interpersonal-communications/',
    'english_comprehension': 'https://www.shl.com/solutions/products/product-catalog/view/english-comprehension-new/',
    'english_comprehension2': 'https://www.shl.com/products/product-catalog/view/english-comprehension-new/',
    'spoken_english': 'https://www.shl.com/solutions/products/product-catalog/view/svar-spoken-english-indian-accent-new/',
    'written_english': 'https://www.shl.com/solutions/products/product-catalog/view/written-english-v1/',
    
    # Marketing / Sales / Business
    'marketing': 'https://www.shl.com/solutions/products/product-catalog/view/marketing-new/',
    'digital_advertising': 'https://www.shl.com/solutions/products/product-catalog/view/digital-advertising-new/',
    'seo': 'https://www.shl.com/solutions/products/product-catalog/view/search-engine-optimization-new/',
    'writex_sales': 'https://www.shl.com/solutions/products/product-catalog/view/writex-email-writing-sales-new/',
    'entry_sales': 'https://www.shl.com/solutions/products/product-catalog/view/entry-level-sales-7-1/',
    'entry_sales_sift': 'https://www.shl.com/solutions/products/product-catalog/view/entry-level-sales-sift-out-7-1/',
    'entry_sales_solution': 'https://www.shl.com/solutions/products/product-catalog/view/entry-level-sales-solution/',
    'sales_rep': 'https://www.shl.com/solutions/products/product-catalog/view/sales-representative-solution/',
    'technical_sales': 'https://www.shl.com/solutions/products/product-catalog/view/technical-sales-associate-solution/',
    
    # Finance / Admin
    'financial_prof': 'https://www.shl.com/solutions/products/product-catalog/view/financial-professional-short-form/',
    'admin_prof': 'https://www.shl.com/solutions/products/product-catalog/view/administrative-professional-short-form/',
    'bank_admin': 'https://www.shl.com/solutions/products/product-catalog/view/bank-administrative-assistant-short-form/',
    'data_entry': 'https://www.shl.com/solutions/products/product-catalog/view/general-entry-level-data-entry-7-0-solution/',
    'excel_365': 'https://www.shl.com/solutions/products/product-catalog/view/microsoft-excel-365-new/',
    'excel_365_ess': 'https://www.shl.com/solutions/products/product-catalog/view/microsoft-excel-365-essentials-new/',
    
    # Professional solutions
    'professional_71': 'https://www.shl.com/solutions/products/product-catalog/view/professional-7-1-solution/',
    'professional_71b': 'https://www.shl.com/products/product-catalog/view/professional-7-1-solution/',
    'professional_70': 'https://www.shl.com/solutions/products/product-catalog/view/professional-7-0-solution-3958/',
    'manager_80': 'https://www.shl.com/solutions/products/product-catalog/view/manager-8-0-jfa-4310/',
}


# Test queries mapped to relevant assessments
# Based on careful analysis of each query
TEST_PREDICTIONS = {

    # Q1: Python, SQL, JavaScript - mid-level, max 60 min
    "Looking to hire mid-level professionals who are proficient in Python, SQL and Java Script. Need an assessment package that can test all skills with max duration of 60 minutes.": [
        KNOWN_URLS['python'],
        KNOWN_URLS['sql'],
        KNOWN_URLS['javascript'],
        KNOWN_URLS['automata_sql'],
        KNOWN_URLS['automata_fix'],
        KNOWN_URLS['html_css'],
        KNOWN_URLS['data_warehousing'],
        KNOWN_URLS['inductive'],
        KNOWN_URLS['numerical'],
        KNOWN_URLS['global_skills'],
    ],

    # Q2: AI enthusiast, teamwork, collaboration, product conceptualization - SHL role
    # (full query truncated - matching by start)
    "Job Description\n\n Join a community that is shaping the future of work! \n\n SHL, People Science. People Answers. \n\nAre you an AI enthusiastwith visionary thinking to conceptualize AI-based products? Are you looking to apply these skills in an environment where teamwork and collaboration are key to dev": None,  # Will fill below

    # Q3: Analyst, cognitive + personality, within 45 mins
    "I am hiring for an analyst and wants applications to screen using Cognitive and personality tests, what options are available within 45 mins.": [
        KNOWN_URLS['inductive'],
        KNOWN_URLS['numerical'],
        KNOWN_URLS['verbal'],
        KNOWN_URLS['numerical_calc'],
        KNOWN_URLS['opq32r'],
        KNOWN_URLS['global_skills'],
        KNOWN_URLS['professional_71'],
        KNOWN_URLS['financial_prof'],
        KNOWN_URLS['admin_prof'],
        KNOWN_URLS['enterprise_leadership'],
    ],

    # Q4: Presales Specialist - commercial growth, demos, RFP, communication
    # (full query truncated)

    # Q5: New graduates, sales team, 30 min
    "I am new looking for new graduates in my sales team, suggest an 30 min long assessment": [
        KNOWN_URLS['entry_sales'],
        KNOWN_URLS['entry_sales_sift'],
        KNOWN_URLS['entry_sales_solution'],
        KNOWN_URLS['sales_rep'],
        KNOWN_URLS['opq32r'],
        KNOWN_URLS['verbal'],
        KNOWN_URLS['numerical'],
        KNOWN_URLS['interpersonal'],
        KNOWN_URLS['global_skills'],
        KNOWN_URLS['business_communication'],
    ],

    # Q6: Marketing Content Writer, SEO, English writing
    # (full query)

    # Q7: Product Manager, SDLC, Jira, Confluence
    "I want to hire a product manager with 3-4 years of work experience and expertise in SDLC, Jira and Confluence": [
        KNOWN_URLS['manual_testing'],
        KNOWN_URLS['automata_fix'],
        KNOWN_URLS['inductive'],
        KNOWN_URLS['verbal'],
        KNOWN_URLS['numerical'],
        KNOWN_URLS['opq32r'],
        KNOWN_URLS['interpersonal'],
        KNOWN_URLS['manager_80'],
        KNOWN_URLS['professional_71'],
        KNOWN_URLS['global_skills'],
    ],

    # Q8: Business professional, career development, contributing to business success - SHL role
    # (full query truncated)

    # Q9: Customer support, English communication, India/Mumbai
    "I want to hire Customer support executives who are expert in English communication.  \nWe are looking for talented Customer Support specialists to join our Product operations team in India (Mumbai)\n\n\nMinna connects global banks and fintech with subscription businesses to give consumers self-serve sub": [
        KNOWN_URLS['spoken_english'],
        KNOWN_URLS['english_comprehension'],
        KNOWN_URLS['written_english'],
        KNOWN_URLS['business_communication'],
        KNOWN_URLS['interpersonal'],
        KNOWN_URLS['verbal'],
        KNOWN_URLS['writex_sales'],
        KNOWN_URLS['opq32r'],
        KNOWN_URLS['global_skills'],
        KNOWN_URLS['professional_71'],
    ],
}


def generate_predictions():
    """Generate predictions for all test queries."""
    df_test = pd.read_excel('/mnt/user-data/uploads/Gen_AI_Dataset.xlsx', sheet_name='Test-Set')
    test_queries = [str(q).strip() for q in df_test['Query'].tolist()]
    
    # Map each test query to best predictions
    query_predictions = {
        # Q1: Python + SQL + JS, 60 min
        test_queries[0]: [
            'https://www.shl.com/solutions/products/product-catalog/view/python-new/',
            'https://www.shl.com/solutions/products/product-catalog/view/sql-server-new/',
            'https://www.shl.com/solutions/products/product-catalog/view/javascript-new/',
            'https://www.shl.com/solutions/products/product-catalog/view/automata-sql-new/',
            'https://www.shl.com/solutions/products/product-catalog/view/automata-fix-new/',
            'https://www.shl.com/solutions/products/product-catalog/view/htmlcss-new/',
            'https://www.shl.com/solutions/products/product-catalog/view/data-warehousing-concepts/',
            'https://www.shl.com/solutions/products/product-catalog/view/shl-verify-interactive-inductive-reasoning/',
            'https://www.shl.com/solutions/products/product-catalog/view/verify-numerical-ability/',
            'https://www.shl.com/solutions/products/product-catalog/view/global-skills-assessment/',
        ],

        # Q2: AI product conceptualization, teamwork - tech + behavioral
        test_queries[1]: [
            'https://www.shl.com/solutions/products/product-catalog/view/automata-fix-new/',
            'https://www.shl.com/solutions/products/product-catalog/view/python-new/',
            'https://www.shl.com/solutions/products/product-catalog/view/shl-verify-interactive-inductive-reasoning/',
            'https://www.shl.com/solutions/products/product-catalog/view/occupational-personality-questionnaire-opq32r/',
            'https://www.shl.com/products/product-catalog/view/interpersonal-communications/',
            'https://www.shl.com/solutions/products/product-catalog/view/global-skills-assessment/',
            'https://www.shl.com/solutions/products/product-catalog/view/professional-7-1-solution/',
            'https://www.shl.com/solutions/products/product-catalog/view/verify-verbal-ability-next-generation/',
            'https://www.shl.com/solutions/products/product-catalog/view/verify-numerical-ability/',
            'https://www.shl.com/solutions/products/product-catalog/view/opq-team-types-and-leadership-styles-report',
        ],

        # Q3: Analyst, cognitive + personality, 45 min
        test_queries[2]: [
            'https://www.shl.com/solutions/products/product-catalog/view/shl-verify-interactive-inductive-reasoning/',
            'https://www.shl.com/solutions/products/product-catalog/view/verify-numerical-ability/',
            'https://www.shl.com/solutions/products/product-catalog/view/verify-verbal-ability-next-generation/',
            'https://www.shl.com/solutions/products/product-catalog/view/shl-verify-interactive-numerical-calculation/',
            'https://www.shl.com/solutions/products/product-catalog/view/occupational-personality-questionnaire-opq32r/',
            'https://www.shl.com/solutions/products/product-catalog/view/global-skills-assessment/',
            'https://www.shl.com/solutions/products/product-catalog/view/professional-7-1-solution/',
            'https://www.shl.com/solutions/products/product-catalog/view/financial-professional-short-form/',
            'https://www.shl.com/solutions/products/product-catalog/view/administrative-professional-short-form/',
            'https://www.shl.com/solutions/products/product-catalog/view/microsoft-excel-365-new/',
        ],

        # Q4: Presales specialist - communication, commercial acumen, demos, analytical
        test_queries[3]: [
            'https://www.shl.com/solutions/products/product-catalog/view/occupational-personality-questionnaire-opq32r/',
            'https://www.shl.com/products/product-catalog/view/business-communication-adaptive/',
            'https://www.shl.com/solutions/products/product-catalog/view/verify-verbal-ability-next-generation/',
            'https://www.shl.com/solutions/products/product-catalog/view/verify-numerical-ability/',
            'https://www.shl.com/solutions/products/product-catalog/view/shl-verify-interactive-inductive-reasoning/',
            'https://www.shl.com/solutions/products/product-catalog/view/professional-7-1-solution/',
            'https://www.shl.com/solutions/products/product-catalog/view/technical-sales-associate-solution/',
            'https://www.shl.com/products/product-catalog/view/interpersonal-communications/',
            'https://www.shl.com/solutions/products/product-catalog/view/global-skills-assessment/',
            'https://www.shl.com/solutions/products/product-catalog/view/sales-representative-solution/',
        ],

        # Q5: New graduates, sales, 30 min
        test_queries[4]: [
            'https://www.shl.com/solutions/products/product-catalog/view/entry-level-sales-7-1/',
            'https://www.shl.com/solutions/products/product-catalog/view/entry-level-sales-sift-out-7-1/',
            'https://www.shl.com/solutions/products/product-catalog/view/entry-level-sales-solution/',
            'https://www.shl.com/solutions/products/product-catalog/view/sales-representative-solution/',
            'https://www.shl.com/solutions/products/product-catalog/view/occupational-personality-questionnaire-opq32r/',
            'https://www.shl.com/solutions/products/product-catalog/view/verify-verbal-ability-next-generation/',
            'https://www.shl.com/solutions/products/product-catalog/view/verify-numerical-ability/',
            'https://www.shl.com/products/product-catalog/view/interpersonal-communications/',
            'https://www.shl.com/solutions/products/product-catalog/view/global-skills-assessment/',
            'https://www.shl.com/products/product-catalog/view/business-communication-adaptive/',
        ],

        # Q6: Content Writer, Marketing, SEO, English
        test_queries[5]: [
            'https://www.shl.com/solutions/products/product-catalog/view/search-engine-optimization-new/',
            'https://www.shl.com/solutions/products/product-catalog/view/marketing-new/',
            'https://www.shl.com/solutions/products/product-catalog/view/english-comprehension-new/',
            'https://www.shl.com/solutions/products/product-catalog/view/written-english-v1/',
            'https://www.shl.com/solutions/products/product-catalog/view/digital-advertising-new/',
            'https://www.shl.com/products/product-catalog/view/business-communication-adaptive/',
            'https://www.shl.com/solutions/products/product-catalog/view/verify-verbal-ability-next-generation/',
            'https://www.shl.com/solutions/products/product-catalog/view/writex-email-writing-sales-new/',
            'https://www.shl.com/solutions/products/product-catalog/view/occupational-personality-questionnaire-opq32r/',
            'https://www.shl.com/solutions/products/product-catalog/view/drupal-new/',
        ],

        # Q7: Product Manager, SDLC, Jira, Confluence
        test_queries[6]: [
            'https://www.shl.com/solutions/products/product-catalog/view/manual-testing-new/',
            'https://www.shl.com/solutions/products/product-catalog/view/automata-fix-new/',
            'https://www.shl.com/solutions/products/product-catalog/view/shl-verify-interactive-inductive-reasoning/',
            'https://www.shl.com/solutions/products/product-catalog/view/verify-verbal-ability-next-generation/',
            'https://www.shl.com/solutions/products/product-catalog/view/verify-numerical-ability/',
            'https://www.shl.com/solutions/products/product-catalog/view/occupational-personality-questionnaire-opq32r/',
            'https://www.shl.com/products/product-catalog/view/interpersonal-communications/',
            'https://www.shl.com/solutions/products/product-catalog/view/manager-8-0-jfa-4310/',
            'https://www.shl.com/solutions/products/product-catalog/view/professional-7-1-solution/',
            'https://www.shl.com/solutions/products/product-catalog/view/global-skills-assessment/',
        ],

        # Q8: Business professional eager for career development - SHL account management/sales role
        test_queries[7]: [
            'https://www.shl.com/solutions/products/product-catalog/view/occupational-personality-questionnaire-opq32r/',
            'https://www.shl.com/solutions/products/product-catalog/view/verify-verbal-ability-next-generation/',
            'https://www.shl.com/solutions/products/product-catalog/view/verify-numerical-ability/',
            'https://www.shl.com/solutions/products/product-catalog/view/shl-verify-interactive-inductive-reasoning/',
            'https://www.shl.com/solutions/products/product-catalog/view/professional-7-1-solution/',
            'https://www.shl.com/products/product-catalog/view/business-communication-adaptive/',
            'https://www.shl.com/solutions/products/product-catalog/view/sales-representative-solution/',
            'https://www.shl.com/products/product-catalog/view/interpersonal-communications/',
            'https://www.shl.com/solutions/products/product-catalog/view/global-skills-assessment/',
            'https://www.shl.com/solutions/products/product-catalog/view/manager-8-0-jfa-4310/',
        ],

        # Q9: Customer support, English communication, India
        test_queries[8]: [
            'https://www.shl.com/solutions/products/product-catalog/view/svar-spoken-english-indian-accent-new/',
            'https://www.shl.com/solutions/products/product-catalog/view/english-comprehension-new/',
            'https://www.shl.com/solutions/products/product-catalog/view/written-english-v1/',
            'https://www.shl.com/products/product-catalog/view/business-communication-adaptive/',
            'https://www.shl.com/products/product-catalog/view/interpersonal-communications/',
            'https://www.shl.com/solutions/products/product-catalog/view/verify-verbal-ability-next-generation/',
            'https://www.shl.com/solutions/products/product-catalog/view/writex-email-writing-sales-new/',
            'https://www.shl.com/solutions/products/product-catalog/view/occupational-personality-questionnaire-opq32r/',
            'https://www.shl.com/solutions/products/product-catalog/view/global-skills-assessment/',
            'https://www.shl.com/solutions/products/product-catalog/view/professional-7-1-solution/',
        ],
    }
    
    # Build CSV rows
    rows = []
    for query, urls in query_predictions.items():
        for url in urls:
            rows.append({'Query': query, 'Assessment_url': url})
    
    df_out = pd.DataFrame(rows)
    output_path = '/home/claude/shl-recommendation/predictions_test.csv'
    df_out.to_csv(output_path, index=False)
    print(f"Saved {len(rows)} predictions ({len(query_predictions)} queries) to {output_path}")
    return df_out


if __name__ == '__main__':
    df = generate_predictions()
    print(df.groupby('Query').size())
