import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from secgym.utils import process_entity_identifiers

class AlertGraph:
    def __init__(self, alerts: pd.DataFrame) -> None:
        """
        Initialize the AlertGraph with a DataFrame of alerts.
        
        :param alerts: DataFrame containing alert entries.
        """
        self.alerts = alerts
        self.graph = nx.Graph()
        self.next_node_id = 0
        self.entity_node_map = {}  # To map (identifier_field, value) to node_id
        self._build_graph()

    def _build_graph(self) -> None:
        """Builds the graph from the DataFrame of alerts and their entities."""
        for idx, alert in self.alerts.iterrows():
            alert_node_id = self.next_node_id
            self.next_node_id += 1

            # Add alert node
            self.graph.add_node(
                alert_node_id,
                type="alert",
                name=alert["AlertName"],
                description=alert["Description"]
            )

            # Process and add entities
            entities = process_entity_identifiers(alert["Entities"])
            self._add_entities_to_graph(entities, alert_node_id)

    def _add_entities_to_graph(self, entities: list, alert_node_id: int) -> None:
        """Adds entities to the graph and connects them to the corresponding alert."""
        for entity in entities:
            node_type, identifier_field, value, extra_info = entity
            entity_key = (identifier_field, value)

            # Check if entity is already added to the graph
            if entity_key not in self.entity_node_map:
                entity_node_id = self.next_node_id
                self.next_node_id += 1

                # Add entity node
                self.graph.add_node(
                    entity_node_id,
                    type="entity",
                    node_type=node_type,
                    identifier_fields=identifier_field,
                    value=value
                )

                # Map entity to its node ID
                self.entity_node_map[entity_key] = entity_node_id
            else:
                # Retrieve existing node ID
                entity_node_id = self.entity_node_map[entity_key]

            # Connect the alert to the entity
            self.graph.add_edge(alert_node_id, entity_node_id)

    def save_to_graphml(self, filepath: str) -> None:
        """
        Saves the graph to a GraphML file.
        
        :param filepath: The path where the GraphML file will be saved.
        """
        nx.write_graphml(self.graph, filepath)
        print(f"Graph saved to {filepath}")

    def plot_custom_graph(self, 
                        root, 
                        figsize=(10, 10), 
                        base_node_size=5000, 
                        max_line_length=20, 
                        show_plot=True, 
                        save_figure=False, 
                        file_path=None,
                        layout='circular'
                        ):
        # Define node sizes and colors based on type
        node_sizes = []
        node_colors = []
        labels = {}

        for node, data in self.graph.nodes(data=True):
            if data.get('type') == 'alert':
                # Show just the alert name
                label = f"ID: {node}\n{data.get('name', '')}"
                
                # Uncomment the following lines to include the description
                # full_description = data.get('description', '')
                # wrapped_description = "\n".join(textwrap.wrap(full_description, max_line_length))
                # label = f"ID: {node}\n{data.get('name', '')}\n{wrapped_description}"
                
                labels[node] = label
                node_sizes.append(base_node_size)  # Size for type alert
                node_colors.append('#ADD8E6')  # Light blue color for type alert
            elif data.get('type') == 'entity':
                # Concatenate identifier_field and value for entities
                identifier_field = data.get('identifier_fields', '')
                value = data.get('value', '')
                label = f"{identifier_field}: {value}"
                labels[node] = label
                node_sizes.append(base_node_size // 3)  # Smaller size for type entity
                node_colors.append('#FFB6C1')  # Light pink color for type entity

        # Define the custom tree layout
        if layout == 'tree':
            pos = self.hierarchy_pos(root)
        elif layout == 'circular':
            pos = nx.circular_layout(self.graph)
        elif not isinstance(layout, str):
            pos = layout
        else:
            raise ValueError("Invalid layout. Choose 'tree' or 'circular'.")
        
        # Set up the figure size
        plt.figure(figsize=figsize)
        
        # Draw the graph
        nx.draw(self.graph, pos=pos, with_labels=True, labels=labels, node_size=node_sizes, node_color=node_colors, font_size=10)

        # Save the plot if required
        if save_figure and file_path is not None:
            plt.savefig(file_path, dpi=600)
        
        # Show the plot if required
        if show_plot:
            plt.show()
        else:
            plt.close()


    # Example usage:
    # graph = AlertGraph(alerts=alert_entries)
    # graph.save_to_graphml("alert_graph.graphml")
    # graph.plot_graph()
