import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from shiny import App, ui, render, reactive
from shinywidgets import output_widget, render_widget

# Load data
prizes = pd.read_csv('https://raw.githubusercontent.com/rfordatascience/tidytuesday/main/data/2025/2025-10-28/prizes.csv')

# Clean gender values
prizes['gender_clean'] = prizes['gender'].str.lower().str.strip()
prizes['gender_clean'] = prizes['gender_clean'].replace({
    'female': 'Women',
    'woman': 'Women', 
    'f': 'Women',
    'male': 'Men',
    'man': 'Men',
    'm': 'Men'
})

app_ui = ui.page_fluid(
    ui.panel_title("Literary Prizes Analysis Dashboard"),
    
    ui.navset_tab(
        # Q1: Genre Analysis
        ui.nav_panel(
            "Q1: Genre Analysis",
            ui.layout_sidebar(
                ui.sidebar(
                    ui.h4("Genre Demographics"),
                    ui.p("Examining representation across literary genres"),
                    width=300
                ),
                ui.card(
                    ui.card_header("Gender Representation by Genre"),
                    output_widget("genre_gender_plot")
                ),
                ui.card(
                    ui.card_header("Ethnic Representation by Genre"),
                    output_widget("genre_ethnicity_plot")
                )
            )
        ),
        
        # Q2: Temporal Trends
        ui.nav_panel(
            "Q2: Temporal Trends",
            ui.layout_sidebar(
                ui.sidebar(
                    ui.h4("Year-over-Year Trends"),
                    ui.p("Has representation improved over time?"),
                    width=300
                ),
                ui.card(
                    ui.card_header("Gender Representation Over Time"),
                    output_widget("temporal_gender_plot")
                ),
                ui.card(
                    ui.card_header("Ethnic Representation Over Time"),
                    output_widget("temporal_ethnicity_plot")
                )
            )
        ),
        
        # Q3: Education Analysis
        ui.nav_panel(
            "Q3: Education & Credentials",
            ui.layout_sidebar(
                ui.sidebar(
                    ui.h4("Filters"),
                    ui.input_select(
                        "filter_gender",
                        "Filter by Gender:",
                        choices=["All", "Women", "Men"]
                    ),
                    ui.input_select(
                        "filter_ethnicity",
                        "Filter by Ethnicity:",
                        choices=["All"] + sorted(prizes['ethnicity_macro'].dropna().unique().tolist())
                    ),
                    ui.input_select(
                        "filter_residence",
                        "Filter by UK Residence:",
                        choices=["All", "Yes", "No"]
                    ),
                    width=300
                ),
                ui.card(
                    ui.card_header("Highest Degree Attained"),
                    output_widget("education_degree_plot")
                ),
                ui.card(
                    ui.card_header("Top Educational Institutions"),
                    output_widget("education_institution_plot")
                ),
                ui.card(
                    ui.card_header("Degree Field Categories"),
                    output_widget("education_field_plot")
                )
            )
        )
    )
)

def server(input, output, session):
    
    # Q1: Genre Analysis - Gender
    @render_widget
    def genre_gender_plot():
        genre_gender = prizes.groupby(['prize_genre', 'gender_clean']).size().reset_index(name='count')
        genre_gender = genre_gender[genre_gender['gender_clean'].isin(['Women', 'Men'])]
        
        fig = px.bar(
            genre_gender,
            x='prize_genre',
            y='count',
            color='gender_clean',
            barmode='group',
            color_discrete_map={'Women': '#e91e63', 'Men': '#2196f3'},
            labels={'prize_genre': 'Genre', 'count': 'Count', 'gender_clean': 'Gender'},
            height=500
        )
        fig.update_layout(xaxis_tickangle=-45)
        return fig
    
    # Q1: Genre Analysis - Ethnicity
    @render_widget
    def genre_ethnicity_plot():
        genre_ethnicity = prizes.groupby(['prize_genre', 'ethnicity_macro']).size().reset_index(name='count')
        genre_ethnicity = genre_ethnicity[genre_ethnicity['ethnicity_macro'].notna()]
        
        fig = px.bar(
            genre_ethnicity,
            x='prize_genre',
            y='count',
            color='ethnicity_macro',
            barmode='group',
            labels={'prize_genre': 'Genre', 'count': 'Count', 'ethnicity_macro': 'Ethnicity'},
            height=500
        )
        fig.update_layout(xaxis_tickangle=-45)
        return fig
    
    # Q2: Temporal Trends - Gender
    @render_widget
    def temporal_gender_plot():
        temporal_gender = prizes.groupby(['prize_year', 'gender_clean']).size().reset_index(name='count')
        temporal_gender = temporal_gender[temporal_gender['gender_clean'].isin(['Women', 'Men'])]
        
        fig = px.line(
            temporal_gender,
            x='prize_year',
            y='count',
            color='gender_clean',
            markers=True,
            color_discrete_map={'Women': '#e91e63', 'Men': '#2196f3'},
            labels={'prize_year': 'Year', 'count': 'Count', 'gender_clean': 'Gender'},
            height=500
        )
        return fig
    
    # Q2: Temporal Trends - Ethnicity
    @render_widget
    def temporal_ethnicity_plot():
        temporal_ethnicity = prizes.groupby(['prize_year', 'ethnicity_macro']).size().reset_index(name='count')
        temporal_ethnicity = temporal_ethnicity[temporal_ethnicity['ethnicity_macro'].notna()]
        
        fig = px.line(
            temporal_ethnicity,
            x='prize_year',
            y='count',
            color='ethnicity_macro',
            markers=True,
            labels={'prize_year': 'Year', 'count': 'Count', 'ethnicity_macro': 'Ethnicity'},
            height=500
        )
        return fig
    
    # Reactive filtered data for Q3
    @reactive.Calc
    def filtered_data():
        df = prizes.copy()
        
        if input.filter_gender() != "All":
            df = df[df['gender_clean'] == input.filter_gender()]
        
        if input.filter_ethnicity() != "All":
            df = df[df['ethnicity_macro'] == input.filter_ethnicity()]
        
        if input.filter_residence() != "All":
            residence_val = 'Yes' if input.filter_residence() == "Yes" else 'No'
            df = df[df['uk_residence'] == residence_val]
        
        return df
    
    # Q3: Education - Degree
    @render_widget
    def education_degree_plot():
        df = filtered_data()
        degree_counts = df.groupby('highest_degree').agg(
            total=('highest_degree', 'size'),
            winners=('person_role', lambda x: (x.str.lower() == 'winner').sum())
        ).reset_index()
        degree_counts = degree_counts.sort_values('total', ascending=False).head(10)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=degree_counts['highest_degree'],
            x=degree_counts['total'],
            name='Total',
            orientation='h',
            marker_color='#8b5cf6'
        ))
        fig.add_trace(go.Bar(
            y=degree_counts['highest_degree'],
            x=degree_counts['winners'],
            name='Winners',
            orientation='h',
            marker_color='#f59e0b'
        ))
        fig.update_layout(
            barmode='group',
            height=500,
            xaxis_title='Count',
            yaxis_title='Degree'
        )
        return fig
    
    # Q3: Education - Institution
    @render_widget
    def education_institution_plot():
        df = filtered_data()
        inst_counts = df['degree_institution'].value_counts().head(15).reset_index()
        inst_counts.columns = ['institution', 'count']
        
        fig = px.bar(
            inst_counts,
            y='institution',
            x='count',
            orientation='h',
            labels={'institution': 'Institution', 'count': 'Count'},
            height=600,
            color='count',
            color_continuous_scale='Viridis'
        )
        fig.update_layout(showlegend=False)
        return fig
    
    # Q3: Education - Field Category
    @render_widget
    def education_field_plot():
        df = filtered_data()
        field_counts = df['degree_field_category'].value_counts().head(12).reset_index()
        field_counts.columns = ['field', 'count']
        
        fig = px.bar(
            field_counts,
            y='field',
            x='count',
            orientation='h',
            labels={'field': 'Field Category', 'count': 'Count'},
            height=500,
            color='count',
            color_continuous_scale='Teal'
        )
        fig.update_layout(showlegend=False)
        return fig

app = App(app_ui, server)
