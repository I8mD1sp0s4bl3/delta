import sys
import dash
import flask
from dash import dcc
from dash import html, Dash, Output, Input, dash_table
# import dash_design_kit as ddk
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly.express as px
import dateutil as du

pd.options.plotting.backend = "plotly"


def to_year_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert a dataframe with a date column to a dataframe with a year column.
    """
    res = df.copy()
    res["year"] = df["date"].dt.year
    return res


def to_decade(year):
    return year // 10 * 10


def generate_dash_table(dataframe: pd.DataFrame, max_rows: int = 10):
    """
    Generates a dash table from a dataframe.
    :param dataframe: the dataframe to generate the table from
    :param max_rows: the number of rows to display
    :return: html.Table
    """
    return dash_table.DataTable(
        dataframe.to_dict('records'),
        columns=[{'id': c, 'name': c} for c in dataframe.columns],
        page_size=max_rows
    )


class Top100BillboardUSA:
    def __init__(self, application: Dash = None):
        # Importing the data
        self.df = self.load_billboard_dataframe()

        # Creating the Dash application
        self.app = Dash(__name__) if application is None else application
        self.app.layout = self.main_layout

        """self.app.layout = ddk.App([
            ddk.Header([
                ddk.Menu(dcc.Link(page['name'], href=page['path']))
                for page in dash.page_registry
            ]),

            dash.page_container
        ])"""

        # Adding callbacks
        self.callbacks()

    @property
    def main_layout(self) -> html.Div:
        """
        Returns the default layout for the Dash application.
        :return: html.Div
        """
        graph_year = [dcc.Graph(id='weeks-on-board-year-{}'.format(i), figure=self.get_weeks_on_board_fig_year(i)) for i in range(1989, 1996)]
        layout = html.Div([
            html.H1('Top 100 Billboard USA'),

            html.H3('Informations à propos des données'),
            dcc.Markdown(f'''
            
            Il s'agit d'un tableau des classements de la Billboard Hebdomadaire des USA de 1958 à 2021,   
            comprenant {len(self.df)} entrées dont {self.song_count} chansons et {self.artist_count} artistes uniques.
            
            
            '''),
            dcc.Graph(id='new_artist_on_board_fig', figure=self.get_new_artist_on_board_fig()),
            dcc.Graph(id='weeks-on-board-plot', figure=self.get_weeks_on_board_fig()),
            dcc.Markdown('''
            Un large pic est visible à la 20e semaine.   
            En grossissant on voit également la 52e semaine sortant de la tendance.   
            Regardons ce même graphique par année. => lien autre page ? [test](/recurrent_rule)   
            Il semblerait que le début des années 90 marque l'arrivée de cette tendance non proportionelle.   
            Il s'avère qu'à la fin de l'année 1991, le Billboard a institué une "règle de récurrence",   
            stipulant que les chansons qui ont figuré au classement pendant 20 semaines sont retirées si elles se classent en dessous de la 50e place.   
            De même pour les chansons au classement depuis 1 an, si elles se trouvent en dessous de la 25e position.   
            '''),
            html.Div([graph_year[0], graph_year[1], graph_year[2], graph_year[3], graph_year[4], graph_year[5], graph_year[6]]),
            html.H3('Graphs by artist'),
            dcc.Dropdown(id="artist-dropdown", options=self.df.artist.unique().tolist(), value='Michael Jackson'),
            html.Div(id='artist-dropdown-output'),
            # html.Div([
            #     "Input: ",
            #     dcc.Input(id='my-input', value='', type='text')
            # ]),
            # html.Table(id='foo'),

            html.H3('Notes'),
            dcc.Markdown('''
            ### Sources   
            https://www.billboard.com/billboard-charts-legend/
            '''),

        ])
        return layout

    def callbacks(self) -> None:
        """
        Adds callbacks to the Dash application.
        :return: None
        """

        # Adding a callback to the artist dropdown
        @self.app.callback(
            Output('artist-dropdown-output', 'children'),
            Input('artist-dropdown', 'value')
        )
        def update_artist_dropdown(input_value):
            # self.generate_artist_gaph(self.df[self.df['artist'] == input_value])
            return generate_dash_table(self.df[self.df['artist'] == input_value])

        # # Example callback
        # @self.app.callback(Output("foo", "children"), Input('my-input', 'value'))
        # def update_graph(input_value):
        #     return html.Div([
        #         html.H2(input_value),
        #         self.generate_table(self.df),
        #     ])

    @staticmethod
    def load_billboard_dataframe() -> pd.DataFrame:
        df = pd.read_csv('data/top_100_billboard_usa.csv')
        df["date"] = pd.to_datetime(df["date"])

        return df


    def get_weeks_on_board_fig_year(self, year):
        """
        Returns a plotly figure of the number of weeks on the billboard for a specific year.
        :return: plotly.graph_objs.Figure
        """
        # 7 years
        df_tmp = self.df[self.df["date"].dt.year == year]
        # Creating the figure
        max_weeks_on_board = df_tmp.groupby(by=["artist", "song"]).max("weeks-on-board").value_counts("weeks-on-board")
        fig = max_weeks_on_board.reindex(range(1, len(max_weeks_on_board))).plot.bar()
        fig.update_layout(showlegend=False)
        fig.update_layout(title="{}".format(year))
        fig.update_layout(xaxis_title="Nombre de semaines consécutives", yaxis_title="Nombre de musiques")

        return fig

    def get_new_artist_on_board_fig(self) -> go.Figure:
        """
        Returns a plotly figure of the number of weeks on the billboard.
        :return: plotly.graph_objs.Figure
        """

        x, y = [], []
        for year in self.df["date"].dt.year.unique():
            filtered_decade_df = self.df[self.df["date"].dt.year == year]
            artistes_distincts_decade = len(filtered_decade_df["artist"].unique())

            x.append(year), y.append(artistes_distincts_decade)

        # Creating the figure
        return px.line(title="Nombre de nouvels artistes chaque année", x=x, y=y,
                       labels={'x': 'Années', 'y': 'Nombre de nouvels artistes'})

    @property
    def artist_count(self): return len(self.df["artist"].unique())

    @property
    def song_count(self): return len(self.df["song"].unique())


if __name__ == '__main__':
    nrg = Top100BillboardUSA()
    nrg.app.run_server(debug=True)
