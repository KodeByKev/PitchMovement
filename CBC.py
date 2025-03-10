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
    "Changeup": "lime",    # Changeup
    "Curveball": "blue",    # Curveball
    "Slider": "gold",  # Slider (darker yellow)
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
    
    # Input fields with Pitch at the top
    html.Div([
        html.Label("Pitch", style={'fontFamily': 'Roboto'}),
        dcc.Dropdown(
            id="pitch-type",
            options=[{"label": pitch, "value": pitch} for pitch in pitch_types],
            value="Fastball",  # Default value
            clearable=False  # Prevent users from clearing the selection
        ),
        
        # Swapped order of vertical and horizontal input boxes
        html.Label("Vertical (IN)", style={'fontFamily': 'Roboto'}),
        dcc.Input(id="vertical-movement", type="number", value=0),
        
        html.Label("Horizontal (IN)", style={'fontFamily': 'Roboto'}),
        dcc.Input(id="horizontal-movement", type="number", value=0),
        
        html.Label("Velo (MPH)", style={'fontFamily': 'Roboto'}),
        dcc.Input(id="pitch-speed", type="number", value=0),  # Fixed type="number"
        
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
    
    # Delete Last Drawing Button
    html.Button('Delete Last Drawing', id='delete-last-drawing', n_clicks=0, style={'fontFamily': 'Roboto', 'margin': '10px'}),
    
    # Add Shaded Circle Section
    html.Div([
        html.Label("Add Shaded Circle", style={'fontFamily': 'Roboto'}),
        html.Label("Center X (IN)", style={'fontFamily': 'Roboto'}),
        dcc.Input(id="circle-x", type="number", value=0),
        html.Label("Center Y (IN)", style={'fontFamily': 'Roboto'}),
        dcc.Input(id="circle-y", type="number", value=0),
        html.Label("Radius (IN)", style={'fontFamily': 'Roboto'}),
        dcc.Input(id="circle-radius", type="number", value=0),
        html.Button('Add Shaded Circle', id='add-shaded-circle', n_clicks=0, style={'fontFamily': 'Roboto', 'margin': '10px'})
    ], style={'marginBottom': '10px'}),
    
    # Delete Most Recent Shaded Circle Button
    html.Button('Delete Most Recent Shaded Circle', id='delete-most-recent-shaded-circle', n_clicks=0, style={'fontFamily': 'Roboto', 'margin': '10px'}),
    
    # Graph
    dcc.Graph(
        id='movement-graph',
        config={
            'modeBarButtonsToAdd': ['drawopenpath'],  # Enable freehand drawing
            'modeBarButtonsToRemove': [
                'zoom2d', 'pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d',
                'hoverClosestCartesian', 'hoverCompareCartesian', 'toggleSpikelines'
            ],  # Remove all other tools
            'toImageButtonOptions': {
                'format': 'png',  # Ensure the download button saves as PNG
                'filename': 'pitch_movement_visualization',  # Default filename
            },
            'scrollZoom': False  # Disable zooming
        }
    ),
    
    # Hidden div to store the data
    html.Div(id='data-store', style={'display': 'none'}),
    
    # Hidden div to store the drawing shapes
    dcc.Store(id='drawing-store', data=[]),
    
    # Hidden div to store the shaded circles
    dcc.Store(id='shaded-circles-store', data=[])
])


# Callback to update the graph and data store
# Callback to update the graph and data store
@app.callback(
    [Output('movement-graph', 'figure'),
     Output('data-store', 'children'),
     Output('drawing-store', 'data'),
     Output('shaded-circles-store', 'data')],
    [Input('add-point', 'n_clicks'),
     Input('delete-recent', 'n_clicks'),
     Input('delete-all', 'n_clicks'),
     Input('reset-axes', 'n_clicks'),
     Input('movement-graph', 'relayoutData'),  # Capture drawing events
     Input('delete-last-drawing', 'n_clicks'),  # Handle delete last drawing button
     Input('add-shaded-circle', 'n_clicks'),  # Handle add shaded circle button
     Input('delete-most-recent-shaded-circle', 'n_clicks'),  # Handle delete most recent shaded circle button
     Input('athlete-name', 'value')],  # Capture Athlete Name input
    [State('horizontal-movement', 'value'),
     State('vertical-movement', 'value'),
     State('pitch-speed', 'value'),
     State('pitch-type', 'value'),  # Corrected ID: pitch-type
     State('draw-color', 'value'),  # Get selected drawing color
     State('circle-x', 'value'),  # Get circle center X
     State('circle-y', 'value'),  # Get circle center Y
     State('circle-radius', 'value'),  # Get circle radius
     State('data-store', 'children'),
     State('drawing-store', 'data'),
     State('shaded-circles-store', 'data')]
)
def update_graph(add_clicks, delete_recent_clicks, delete_all_clicks, reset_axes_clicks, relayoutData, delete_last_drawing_clicks, add_shaded_circle_clicks, delete_most_recent_shaded_circle_clicks, athlete_name, vertical, horizontal, speed, pitch_type, draw_color, circle_x, circle_y, circle_radius, data_store, drawing_store, shaded_circles_store):
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
    elif button_id == 'delete-last-drawing' and delete_last_drawing_clicks > 0 and drawing_store:
        # Delete the last drawing
        drawing_store = drawing_store[:-1]  # Remove the last shape
    elif button_id == 'add-shaded-circle' and add_shaded_circle_clicks > 0:
        # Add a shaded circle with the selected draw color
        new_circle = {
            'type': 'circle',
            'x0': circle_x - circle_radius,
            'x1': circle_x + circle_radius,
            'y0': circle_y - circle_radius,
            'y1': circle_y + circle_radius,
            'line': {'color': draw_color, 'width': 2},
            'fillcolor': draw_color,
            'opacity': 0.3,  # Shaded circle
            'layer': 'below'
        }
        shaded_circles_store.append(new_circle)
    elif button_id == 'delete-most-recent-shaded-circle' and delete_most_recent_shaded_circle_clicks > 0 and shaded_circles_store:
        # Delete the most recent shaded circle
        shaded_circles_store = shaded_circles_store[:-1]  # Remove the last shaded circle
    
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
                     title=f"{athlete_name} Pitch Movement Visualization" if athlete_name else "Pitch Movement Visualization",
                     size_max=20,  # Increase dot size
                     color_discrete_map=pitch_colors)  # Use custom pitch colors
    
    # Update layout for a cool font and larger dots
    fig.update_traces(marker=dict(size=15))  # Set data points size to 15
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
    
    # Add dotted circles for the variance
    for var in variance_data:
        if not np.isnan(var['Horizontal Variance']) and not np.isnan(var['Vertical Variance']):
            # Get the color for the pitch type
            color = pitch_colors[var['Pitch']]
            
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
    if relayoutData and 'shapes' in relayoutData:
        # Get the new shape from the drawing event
        new_shape = relayoutData['shapes'][-1]
        # Set the color of the new shape to the selected draw_color
        new_shape['line'] = {'color': draw_color, 'width': 2}
        # Add the new shape to the drawing store
        drawing_store.append(new_shape)
    
    # Add all drawing shapes to the figure
    for shape in drawing_store:
        fig.add_shape(shape)
    
    # Add all shaded circles to the figure
    for circle in shaded_circles_store:
        fig.add_shape(circle)
    
    # Update the data store and drawing store
    data_json = data.to_json(orient='split')
    
    return fig, data_json, drawing_store, shaded_circles_store


server = app.server

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
