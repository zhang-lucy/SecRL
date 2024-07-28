import networkx as nx
import matplotlib.pyplot as plt
import textwrap

class SOCGraph:
    def __init__(self):
        self.G = nx.Graph()
        self.node_counter = 0
    
    def add_investigation(self, description, from_ioc_id=None):
        # Create a new investigation node with a unique ID
        self.node_counter += 1
        investigation_id = self.node_counter
        self.G.add_node(investigation_id, type='Investigation', description=description)
        
        # If the investigation is related to an existing IoC, add an edge between them
        if from_ioc_id is not None and self.G.has_node(from_ioc_id) and self.G.nodes[from_ioc_id]['type'] == 'IoC':
            self.G.add_edge(investigation_id, from_ioc_id)
        
        return investigation_id

    def delete_investigation(self, investigation_id):
        if self.G.has_node(investigation_id) and self.G.nodes[investigation_id]['type'] == 'Investigation':
            self.G.remove_node(investigation_id)
    
    def add_ioc(self, description, from_investigation_id=None):
        # Create a new IoC node with a unique ID
        self.node_counter += 1
        ioc_id = self.node_counter
        self.G.add_node(ioc_id, type='IoC', description=description)
        
        # If the IoC is related to an existing investigation, add an edge between them
        if from_investigation_id is not None and self.G.has_node(from_investigation_id) and self.G.nodes[from_investigation_id]['type'] == 'Investigation':
            self.G.add_edge(ioc_id, from_investigation_id)
        
        return ioc_id
    
    def delete_ioc(self, ioc_id):
        if self.G.has_node(ioc_id) and self.G.nodes[ioc_id]['type'] == 'IoC':
            self.G.remove_node(ioc_id)

    def plot_custom_graph(self, root, figsize=(10, 10), base_node_size=5000, max_line_length=20):
        # Define node sizes and colors based on type
        node_sizes = []
        node_colors = []
        labels = {}

        for node, data in self.G.nodes(data=True):
            full_description = data['description']
            wrapped_description = "\n".join(textwrap.wrap(full_description, max_line_length))
            label = f"ID: {node}\n{wrapped_description}"
            labels[node] = label
            
            if data.get('type') == 'Investigation':
                node_sizes.append(base_node_size)  # Size for type Investigation
                node_colors.append('#ADD8E6')  # Light blue color for type Investigation
            elif data.get('type') == 'IoC':
                node_sizes.append(base_node_size // 3)  # Smaller size for type IoC
                node_colors.append('#FFB6C1')  # Light pink color for type IoC

        # Define the custom tree layout
        pos = self.hierarchy_pos(root)
        
        # Set up the figure size
        plt.figure(figsize=figsize)
        
        # Draw the graph
        nx.draw(self.G, pos, with_labels=True, labels=labels, node_size=node_sizes, node_color=node_colors, font_size=10)

        # Show the plot
        plt.show()
    
    def hierarchy_pos(self, root):
        def _hierarchy_pos(G, root, width=1., vert_gap=0.2, vert_loc=0, xcenter=0.5, pos=None, parent=None):
            if pos is None:
                pos = {root: (xcenter, vert_loc)}
            else:
                pos[root] = (xcenter, vert_loc)
            neighbors = list(G.neighbors(root))
            if parent is not None:
                neighbors.remove(parent)  
            if len(neighbors) != 0:
                dx = width / len(neighbors) 
                nextx = xcenter - width / 2 - dx / 2
                for neighbor in neighbors:
                    nextx += dx
                    pos = _hierarchy_pos(G, neighbor, width=dx, vert_gap=vert_gap, 
                                         vert_loc=vert_loc-vert_gap, xcenter=nextx, pos=pos, parent=root)
            return pos
        
        return _hierarchy_pos(self.G, root)