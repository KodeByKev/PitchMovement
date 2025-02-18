import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import pandas as pd
import numpy as np

# Initialize the Dash app
app = dash.Dash(__name__)

# Define the pitch types in the specified order
pitch_types = [
    "Fastball", "Changeup", "Curveball", "Slider", "Sinker", 
    "Splitter", "Cutter", "Circle Change", "Knuckle Curve", "Slurve", 
    "Sweeper", "Knuckleball"
]

# Define the custom color mapping for pitch types
pitch_colors = {
    "Fastball": "red",        # Fastball
    "Changeup": "green",    # Changeup
    "Curveball": "blue",    # Curveball
    "Slider": "yellow",     # Slider
    "Sinker": "orange",     # Sinker
    "Splitter": "teal",     # Splitter
    "Cutter": "saddlebrown",  # Cutter
    "Sweeper": "goldenrod",   # Sweeper
    "Circle Change": "purple",
    "Knuckle Curve": "pink",
    "Slurve": "cyan",
    "Knuckleball": "gray"
}

# Layout of the app
app.layout = html.Div([
    # Logo
    html.Img(src=app.get_asset_url('CBClogo.png'), style={'height': '100px', 'margin': '10px'}),
    
    # Title
    html.H1("Chapman Baseball Compound", style={'fontFamily': 'Roboto', 'color': 'darkblue'}),
    
    # Athlete Name Input
    html.Div([
        html.Label("Athlete Name", style={'fontFamily': 'Roboto'}),
        dcc.Input(id="athlete-name", type="text", value="", placeholder="Enter Athlete Name"),
    ], style={'marginBottom': '10px'}),
    
    # Subtitle
    html.H2(id='subtitle', style={'fontFamily': 'Roboto', 'color': 'darkblue'}),
    
    # Input fields with Pitch at the top
    html.Div([
        html.Label("Pitch", style={'fontFamily': 'Roboto'}),
        dcc.Dropdown(
            id="pitch-type",
            options=[{"label": pitch, "value": pitch} for pitch in pitch_types],
            value="Fastball",  # Default value
            clearable=False  # Prevent users from clearing the selection
        ),
        
        html.Label("Horizontal (IN)", style={'fontFamily': 'Roboto'}),
        dcc.Input(id="horizontal-movement", type="number", value=0),
        
        html.Label("Vertical (IN)", style={'fontFamily': 'Roboto'}),
        dcc.Input(id="vertical-movement", type="number", value=0),
        
        html.Label("Velo (MPH)", style={'fontFamily': 'Roboto'}),
        dcc.Input(id="pitch-speed", type="number", value=0),
        
        html.Button('Add Data Point', id='add-point', n_clicks=0, style={'fontFamily': 'Roboto', 'margin': '10px'}),
        html.Button('Delete Most Recent Point', id='delete-recent', n_clicks=0, style={'fontFamily': 'Roboto', 'margin': '10px'}),
        html.Button('Delete All Data', id='delete-all', n_clicks=0, style={'fontFamily': 'Roboto', 'margin': '10px'}),
        html.Button('Reset Axes', id='reset-axes', n_clicks=0, style={'fontFamily': 'Roboto', 'margin': '10px'})
    ]),
    
    # Drawing tool
    html.Label("Select Draw Color (Pitch Type)", style={'fontFamily': 'Roboto'}),
    dcc.Dropdown(
        id="draw-color",
        options=[{"label": pitch, "value": pitch_colors[pitch]} for pitch in pitch_types],
        value="red",  # Default color
        clearable=False
    ),
    
    # Graph
    dcc.Graph(
        id='movement-graph',
        config={
            'modeBarButtonsToAdd': ['drawopenpath'],  # Enable freehand drawing
            'scrollZoom': True  # Allow zooming
        }
    ),
    
    # Hidden div to store the data
    html.Div(id='data-store', style={'display': 'none'})
])

# Callback to update the subtitle
@app.callback(
    Output('subtitle', 'children'),
    [Input('athlete-name', 'value')]
)
def update_subtitle(athlete_name):
    return f"{athlete_name} Pitch Movement Visualization"

# Callback to update the graph and data store
@app.callback(
    [Output('movement-graph', 'figure'),
     Output('data-store', 'children')],
    [Input('add-point', 'n_clicks'),
     Input('delete-recent', 'n_clicks'),
     Input('delete-all', 'n_clicks'),
     Input('reset-axes', 'n_clicks'),
     Input('movement-graph', 'relayoutData')],  # Capture drawing events
    [State('horizontal-movement', 'value'),
     State('vertical-movement', 'value'),
     State('pitch-speed', 'value'),
     State('pitch-type', 'value'),
     State('draw-color', 'value'),  # Get selected drawing color
     State('data-store', 'children')]
)
def update_graph(add_clicks, delete_recent_clicks, delete_all_clicks, reset_axes_clicks, relayout_data, vertical, horizontal, speed, pitch_type, draw_color, data_store):
    # Initialize an empty DataFrame if no data exists
    if data_store is None:
        data = pd.DataFrame(columns=['Horizontal (IN)', 'Vertical (IN)', 'Velo (MPH)', 'Pitch', 'Pitch#'])
    else:
        data = pd.read_json(data_store, orient='split')
    
    # Determine which button was clicked
    ctx = dash.callback_context
    if not ctx.triggered:
        button_id = None
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Handle button actions
    if button_id == 'add-point' and add_clicks > 0:
        # Add new data point with Pitch# based on index + 1
        new_data = pd.DataFrame({
            'Horizontal (IN)': [vertical],
            'Vertical (IN)': [horizontal],
            'Velo (MPH)': [speed],
            'Pitch': [pitch_type],
            'Pitch#': [len(data) + 1]
        })
        data = pd.concat([data, new_data], ignore_index=True)
    elif button_id == 'delete-recent' and delete_recent_clicks > 0 and not data.empty:
        # Delete the most recent data point
        data = data.iloc[:-1]  # Remove the last row
    elif button_id == 'delete-all' and delete_all_clicks > 0:
        # Delete all data
        data = pd.DataFrame(columns=['Horizontal (IN)', 'Vertical (IN)', 'Velo (MPH)', 'Pitch', 'Pitch#'])
    
    # Calculate variance and mean for each pitch type
    variance_data = []
    for pitch in data['Pitch'].unique():
        pitch_data = data[data['Pitch'] == pitch]
        horizontal_var = pitch_data['Horizontal (IN)'].var()
        vertical_var = pitch_data['Vertical (IN)'].var()
        variance_data.append({
            'Pitch': pitch,
            'Horizontal Variance': horizontal_var,
            'Vertical Variance': vertical_var,
            'Vertical Mean': pitch_data['Vertical (IN)'].mean(),
            'Horizontal Mean': pitch_data['Horizontal (IN)'].mean()
        })
    
    # Create the figure
    fig = px.scatter(data, x='Horizontal (IN)', y='Vertical (IN)', 
                     color='Pitch', hover_data=['Velo (MPH)', 'Pitch', 'Pitch#'],
                     title="Pitch Movement Visualization",
                     size_max=20,  # Increase dot size
                     color_discrete_map=pitch_colors)  # Use custom pitch colors
    
    # Update layout for a cool font and larger dots
    fig.update_traces(marker=dict(size=12))  # Larger dots
    fig.update_layout(
        font_family="Roboto",
        title_font_size=24,
        title_font_color="darkblue",
        xaxis_title="Horizontal (IN)",
        yaxis_title="Vertical (IN)",
        xaxis=dict(
            title_font=dict(size=18, family="Roboto"),
            range=[-20, 20],  # Fixed x-axis range
            scaleanchor="y",  # Ensure x and y axes are scaled equally
            scaleratio=1,  # Maintain a 1:1 aspect ratio
            showgrid=True,
            gridcolor="lightgray",  # Light gray gridlines
            gridwidth=1,  # Thin gridlines
            zeroline=True,  # Show the x=0 line
            zerolinewidth=2,  # Bold x=0 line
            zerolinecolor='black'  # Color of the x=0 line
        ),
        yaxis=dict(
            title_font=dict(size=18, family="Roboto"),
            range=[-20, 20],  # Fixed y-axis range
            showgrid=True,
            gridcolor="lightgray",  # Light gray gridlines
            gridwidth=1,  # Thin gridlines
            zeroline=True,  # Show the y=0 line
            zerolinewidth=2,  # Bold y=0 line
            zerolinecolor='black'  # Color of the y=0 line
        ),
        plot_bgcolor='white',  # Set background color to white
        width=800,  # Set a fixed width for the graph
        height=800  # Set a fixed height for the graph (to make it square)
    )
    
    # Add shaded circles for the average and dotted lines for the variance
    for var in variance_data:
        if not np.isnan(var['Horizontal Variance']) and not np.isnan(var['Vertical Variance']):
            # Get the color for the pitch type
            color = pitch_colors[var['Pitch']]
            
            # Add shaded circle for the average
            fig.add_shape(
                type="circle",
                x0=var['Horizontal Mean'] - 1,  # Small radius for average
                x1=var['Horizontal Mean'] + 1,
                y0=var['Vertical Mean'] - 1,
                y1=var['Vertical Mean'] + 1,
                line=dict(color=color, width=2),
                fillcolor=color,
                opacity=0.3,  # Shaded circle for average
                layer="below"
            )
            
            # Add dotted circle for the variance
            fig.add_shape(
                type="circle",
                x0=var['Horizontal Mean'] - np.sqrt(var['Horizontal Variance']),
                x1=var['Horizontal Mean'] + np.sqrt(var['Horizontal Variance']),
                y0=var['Vertical Mean'] - np.sqrt(var['Vertical Variance']),
                y1=var['Vertical Mean'] + np.sqrt(var['Vertical Variance']),
                line=dict(color=color, width=2, dash='dot'),  # Dotted line for variance
                layer="below"
            )
    
    # Handle drawing events
    if relayout_data and 'shapes' in relayout_data:
        for shape in relayout_data['shapes']:
            # Set the color of the drawn shape to the selected color
            shape['line'] = {'color': draw_color, 'width': 2}
            fig.add_shape(shape)
    
    # Update the data store
    data_json = data.to_json(orient='split')
    
    return fig, data_json

server = app.server

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
