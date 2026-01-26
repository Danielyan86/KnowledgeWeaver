// Knowledge Graph Visualization using D3.js
class KnowledgeGraph {
    constructor(containerId, svgId, options = {}) {
        this.containerId = containerId;
        this.svgId = svgId;
        this.svg = null;
        this.simulation = null;
        this.nodes = [];
        this.links = [];
        this.zoom = null;
        this.g = null;
        this.nodeElements = null;
        this.linkElements = null;
        this.labelElements = null;
        this.selectedNode = null;
        
        // 使用规范化器（如果可用）
        this.normalizer = options.normalizer || null;
        this.config = options.config || (typeof KG_CONFIG !== 'undefined' ? KG_CONFIG : null);
        
        // 使用配置的颜色映射
        if (this.config && this.config.NODE_TYPES) {
            const nodeTypes = Object.keys(this.config.NODE_TYPES);
            const colors = nodeTypes.map(type => this.config.NODE_TYPES[type].color);
            this.colorScale = d3.scaleOrdinal(colors);
            this.nodeTypeMap = new Map(nodeTypes.map(type => [type, this.config.NODE_TYPES[type]]));
        } else {
            this.colorScale = d3.scaleOrdinal(d3.schemeCategory10);
            this.nodeTypeMap = new Map();
        }
    }

    init() {
        const container = document.getElementById(this.containerId);
        const svgElement = document.getElementById(this.svgId);

        if (!container || !svgElement) {
            console.error('Graph container or SVG element not found');
            return;
        }

        const width = container.clientWidth;
        const height = container.clientHeight || 500;

        this.svg = d3.select(`#${this.svgId}`)
            .attr('width', '100%')
            .attr('height', '100%')
            .attr('viewBox', [0, 0, width, height]);

        // Add zoom behavior
        this.zoom = d3.zoom()
            .scaleExtent([0.1, 10])
            .on('zoom', (event) => {
                this.g.attr('transform', event.transform);
            });

        this.svg.call(this.zoom);

        // Create main group for all elements
        this.g = this.svg.append('g');

        // Add arrow marker for directed edges
        this.svg.append('defs').append('marker')
            .attr('id', 'arrowhead')
            .attr('viewBox', '-0 -3 6 6')
            .attr('refX', 16)
            .attr('refY', 0)
            .attr('orient', 'auto')
            .attr('markerWidth', 4)
            .attr('markerHeight', 4)
            .append('path')
            .attr('d', 'M 0,-3 L 6,0 L 0,3')
            .attr('fill', '#bbb');

        // Initialize force simulation
        const linkDistance = this.config?.VISUALIZATION?.LAYOUT?.LINK_DISTANCE || 
                            (typeof CONFIG !== 'undefined' ? CONFIG.GRAPH_VIS.LINK_DISTANCE : 80);
        const chargeStrength = this.config?.VISUALIZATION?.LAYOUT?.CHARGE_STRENGTH || 
                              (typeof CONFIG !== 'undefined' ? CONFIG.GRAPH_VIS.CHARGE_STRENGTH : -300);
        const collisionRadius = this.config?.VISUALIZATION?.LAYOUT?.COLLISION_RADIUS || 30;
        const centerStrength = this.config?.VISUALIZATION?.LAYOUT?.CENTER_STRENGTH || 0.05;
        
        this.simulation = d3.forceSimulation()
            .force('link', d3.forceLink().id(d => d.id).distance(linkDistance))
            .force('charge', d3.forceManyBody().strength(chargeStrength))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide().radius(collisionRadius))
            .force('x', d3.forceX(width / 2).strength(centerStrength))
            .force('y', d3.forceY(height / 2).strength(centerStrength));

        this.width = width;
        this.height = height;
    }

    async loadGraph(useFilter = false) {
        try {
            let data;

            if (useFilter) {
                // 标签过滤模式（用于概览）
                const labelsResponse = await fetch(buildApiUrl(CONFIG.ENDPOINTS.GRAPH_POPULAR) + '?limit=30');
                if (!labelsResponse.ok) {
                    throw new Error(`Failed to get labels: ${labelsResponse.status}`);
                }
                const labels = await labelsResponse.json();

                if (!labels || labels.length === 0) {
                    console.log('No graph labels found');
                    return false;
                }

                // Fetch graph data for top labels and merge them
                const allNodes = new Map();
                const allEdges = [];
                const seenEdges = new Set();

                const labelsToFetch = labels.slice(0, 15);
                const graphPromises = labelsToFetch.map(label =>
                    fetch(buildApiUrl(CONFIG.ENDPOINTS.GRAPH) + `?label=${encodeURIComponent(label)}`)
                        .then(res => res.ok ? res.json() : null)
                        .catch(() => null)
                );

                const graphResults = await Promise.all(graphPromises);

                graphResults.forEach(result => {
                    if (!result) return;

                    if (result.nodes && Array.isArray(result.nodes)) {
                        result.nodes.forEach(node => {
                            const nodeId = node.id || node.labels?.[0];
                            if (nodeId && !allNodes.has(nodeId)) {
                                allNodes.set(nodeId, node);
                            }
                        });
                    }

                    if (result.edges && Array.isArray(result.edges)) {
                        result.edges.forEach(edge => {
                            const edgeKey = `${edge.source}-${edge.target}`;
                            if (!seenEdges.has(edgeKey)) {
                                seenEdges.add(edgeKey);
                                allEdges.push(edge);
                            }
                        });
                    }
                });

                data = {
                    nodes: Array.from(allNodes.values()),
                    edges: allEdges
                };
            } else {
                // 完整图谱模式（默认）
                const response = await fetch(buildApiUrl(CONFIG.ENDPOINTS.GRAPH));
                if (!response.ok) {
                    throw new Error(`Failed to load graph: ${response.status}`);
                }
                data = await response.json();
            }

            if (!data || !data.nodes || data.nodes.length === 0) {
                console.log('No graph data available');
                return false;
            }

            console.log(`Loaded graph: ${data.nodes.length} nodes, ${data.edges?.length || 0} edges`);

            this.processGraphData(data);
            this.render();
            return true;
        } catch (error) {
            console.error('Failed to load graph:', error);
            throw error;
        }
    }

    processGraphData(data) {
        // 如果使用规范化器，先规范化数据
        let processedData = data;
        if (this.normalizer && typeof this.normalizer.normalizeGraph === 'function') {
            try {
                const normalized = this.normalizer.normalizeGraph(data);
                processedData = normalized;
                console.log('Graph normalized:', normalized.stats || {});
            } catch (error) {
                console.warn('Normalization failed, using original data:', error);
                processedData = data;
            }
        }
        
        // LightRAG returns data in format: { nodes: [...], edges: [...] }
        const nodeMap = new Map();

        // Process nodes
        if (processedData.nodes && Array.isArray(processedData.nodes)) {
            processedData.nodes.forEach(node => {
                // LightRAG format: node.id is the main identifier, node.labels is array, node.properties has details
                const nodeId = node.id || node.labels?.[0] || node.entity_name || node.name;
                if (nodeId && !nodeMap.has(nodeId)) {
                    const props = node.properties || {};
                    const nodeType = props.entity_type || node.type || 'Entity';
                    
                    nodeMap.set(nodeId, {
                        id: nodeId,
                        label: node.label || nodeId,
                        type: nodeType,
                        description: props.description || node.description || '',
                        properties: props,
                        degree: node.degree || 0
                    });
                }
            });
        }

        // Process edges/relationships
        this.links = [];
        if (processedData.edges && Array.isArray(processedData.edges)) {
            processedData.edges.forEach(edge => {
                const source = edge.source || edge.src_id || edge.from;
                const target = edge.target || edge.tgt_id || edge.to;

                if (source && target && source !== target) {
                    // Ensure source and target nodes exist
                    if (!nodeMap.has(source)) {
                        nodeMap.set(source, {
                            id: source,
                            label: source,
                            type: 'Entity',
                            description: '',
                            properties: {},
                            degree: 0
                        });
                    }
                    if (!nodeMap.has(target)) {
                        nodeMap.set(target, {
                            id: target,
                            label: target,
                            type: 'Entity',
                            description: '',
                            properties: {},
                            degree: 0
                        });
                    }

                    // Increment degree counts
                    nodeMap.get(source).degree++;
                    nodeMap.get(target).degree++;

                    // Get edge properties - 使用规范化后的关系标签
                    const edgeProps = edge.properties || {};
                    const relationLabel = edge.label || 
                                        edgeProps.description || 
                                        edge.description || 
                                        edge.relation || 
                                        '';
                    
                    // 限制关系标签长度
                    const maxRelationLength = this.config?.VISUALIZATION?.EDGE?.MAX_LABEL_LENGTH || 12;
                    const displayLabel = relationLabel.length > maxRelationLength 
                        ? relationLabel.substring(0, maxRelationLength) + '...' 
                        : relationLabel;
                    
                    this.links.push({
                        source: source,
                        target: target,
                        label: displayLabel,
                        originalLabel: relationLabel, // 保留原始标签
                        weight: edgeProps.weight || edge.weight || 1
                    });
                }
            });
        }

        this.nodes = Array.from(nodeMap.values());

        // Calculate node radius based on degree
        const maxDegree = Math.max(...this.nodes.map(n => n.degree), 1);
        const minRadius = this.config?.VISUALIZATION?.NODE?.MIN_RADIUS || 
                         (typeof CONFIG !== 'undefined' ? CONFIG.GRAPH_VIS.NODE_RADIUS_MIN : 8);
        const maxRadius = this.config?.VISUALIZATION?.NODE?.MAX_RADIUS || 
                         (typeof CONFIG !== 'undefined' ? CONFIG.GRAPH_VIS.NODE_RADIUS_MAX : 25);
        
        const radiusScale = d3.scaleLinear()
            .domain([0, maxDegree])
            .range([minRadius, maxRadius]);

        this.nodes.forEach(node => {
            node.radius = radiusScale(node.degree);
        });
    }

    render() {
        if (!this.g) {
            this.init();
        }

        // Stop any existing simulation first to prevent updates to old elements
        if (this.simulation) {
            this.simulation.stop();
            this.simulation.on('tick', null);
        }

        // Clear previous elements - more thorough
        this.g.selectAll('*').remove();
        // Also ensure all specific element types are removed
        this.g.selectAll('g.links, g.nodes, g.labels, g.link-labels').remove();
        this.g.selectAll('line, circle, text').remove();

        // Create links
        const edgeColor = this.config?.VISUALIZATION?.EDGE?.STROKE_COLOR || '#999';
        const edgeOpacity = this.config?.VISUALIZATION?.EDGE?.STROKE_OPACITY || 0.6;
        const minEdgeWidth = this.config?.VISUALIZATION?.EDGE?.STROKE_WIDTH_MIN || 1;
        const maxEdgeWidth = this.config?.VISUALIZATION?.EDGE?.STROKE_WIDTH_MAX || 4;
        
        // 计算边的宽度范围
        const maxWeight = Math.max(...this.links.map(l => l.weight || 1), 1);
        const edgeWidthScale = d3.scaleLinear()
            .domain([0, maxWeight])
            .range([minEdgeWidth, maxEdgeWidth]);
        
        this.linkElements = this.g.append('g')
            .attr('class', 'links')
            .selectAll('line')
            .data(this.links)
            .enter()
            .append('line')
            .attr('class', 'link')
            .attr('stroke', edgeColor)
            .attr('stroke-opacity', edgeOpacity)
            .attr('stroke-width', d => edgeWidthScale(d.weight || 1))
            .attr('marker-end', 'url(#arrowhead)');

        // Create link labels with background for better readability
        const linkFontSize = this.config?.VISUALIZATION?.EDGE?.LABEL_FONT_SIZE || 9;
        const maxLinkLabelLength = this.config?.VISUALIZATION?.EDGE?.MAX_LABEL_LENGTH || 12;

        // Create a group for each link label (background + text)
        const linkLabelGroups = this.g.append('g')
            .attr('class', 'link-labels')
            .selectAll('g')
            .data(this.links)
            .enter()
            .append('g')
            .attr('class', 'link-label-group');

        // Add background rect for each label
        linkLabelGroups.append('rect')
            .attr('class', 'link-label-bg')
            .attr('fill', 'white')
            .attr('fill-opacity', 0.85)
            .attr('rx', 3)
            .attr('ry', 3);

        // Add text
        const linkLabels = linkLabelGroups.append('text')
            .attr('class', 'link-label')
            .attr('font-size', linkFontSize + 'px')
            .attr('fill', '#555')
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'middle')
            .text(d => {
                const label = d.label || '';
                return label.length > maxLinkLabelLength
                    ? label.substring(0, maxLinkLabelLength) + '...'
                    : label;
            });

        // Update background rect size based on text
        linkLabelGroups.each(function() {
            const group = d3.select(this);
            const text = group.select('text');
            const rect = group.select('rect');

            // Get text bounding box after render
            setTimeout(() => {
                const bbox = text.node()?.getBBox();
                if (bbox) {
                    rect.attr('x', bbox.x - 3)
                        .attr('y', bbox.y - 2)
                        .attr('width', bbox.width + 6)
                        .attr('height', bbox.height + 4);
                }
            }, 100);
        });

        // Create nodes
        const strokeColor = this.config?.VISUALIZATION?.NODE?.STROKE_COLOR || '#fff';
        const strokeWidth = this.config?.VISUALIZATION?.NODE?.STROKE_WIDTH || 2;
        
        this.nodeElements = this.g.append('g')
            .attr('class', 'nodes')
            .selectAll('circle')
            .data(this.nodes)
            .enter()
            .append('circle')
            .attr('class', 'node')
            .attr('r', d => d.radius)
            .attr('fill', d => {
                // 使用配置的颜色映射
                if (this.nodeTypeMap.has(d.type)) {
                    return this.nodeTypeMap.get(d.type).color;
                }
                return this.colorScale(d.type);
            })
            .attr('stroke', strokeColor)
            .attr('stroke-width', strokeWidth)
            .style('cursor', 'pointer')
            .call(this.drag())
            .on('click', (event, d) => this.onNodeClick(event, d))
            .on('mouseover', (event, d) => this.onNodeHover(event, d, true))
            .on('mouseout', (event, d) => this.onNodeHover(event, d, false));

        // Create node labels
        const maxLabelLength = this.config?.VISUALIZATION?.NODE?.MAX_LABEL_LENGTH || 10;
        const minFontSize = this.config?.VISUALIZATION?.NODE?.LABEL_FONT_SIZE_MIN || 10;
        const maxFontSize = this.config?.VISUALIZATION?.NODE?.LABEL_FONT_SIZE_MAX || 14;
        
        this.labelElements = this.g.append('g')
            .attr('class', 'labels')
            .selectAll('text')
            .data(this.nodes)
            .enter()
            .append('text')
            .attr('class', 'node-label')
            .attr('font-size', d => {
                const fontSize = Math.max(minFontSize, Math.min(maxFontSize, d.radius * 0.6));
                return fontSize + 'px';
            })
            .attr('fill', '#333')
            .attr('text-anchor', 'middle')
            .attr('dy', d => d.radius + 12)
            .text(d => {
                const label = d.label || d.id || '';
                return label.length > maxLabelLength 
                    ? label.substring(0, maxLabelLength) + '...' 
                    : label;
            });

        // Ensure simulation exists before updating
        if (!this.simulation) {
            this.init();
        }

        // Update simulation with new data
        this.simulation
            .nodes(this.nodes)
            .on('tick', () => this.ticked(linkLabelGroups));

        this.simulation.force('link').links(this.links);

        // Update center force with current dimensions
        this.simulation.force('center', d3.forceCenter(this.width / 2, this.height / 2));
        this.simulation.force('x', d3.forceX(this.width / 2).strength(0.05));
        this.simulation.force('y', d3.forceY(this.height / 2).strength(0.05));

        // Restart simulation with fresh alpha
        this.simulation.alpha(1).restart();

        // Fit to view after simulation settles
        setTimeout(() => this.fitToView(), 3000);
    }

    fitToView() {
        if (this.nodes.length === 0) return;

        // Calculate bounds
        let minX = Infinity, maxX = -Infinity;
        let minY = Infinity, maxY = -Infinity;

        this.nodes.forEach(node => {
            if (node.x !== undefined && node.y !== undefined) {
                minX = Math.min(minX, node.x);
                maxX = Math.max(maxX, node.x);
                minY = Math.min(minY, node.y);
                maxY = Math.max(maxY, node.y);
            }
        });

        const padding = 50;
        const graphWidth = maxX - minX + padding * 2;
        const graphHeight = maxY - minY + padding * 2;
        const centerX = (minX + maxX) / 2;
        const centerY = (minY + maxY) / 2;

        const scale = Math.min(
            this.width / graphWidth,
            this.height / graphHeight,
            1.5
        ) * 0.9;

        this.svg.transition()
            .duration(750)
            .call(
                this.zoom.transform,
                d3.zoomIdentity
                    .translate(this.width / 2, this.height / 2)
                    .scale(scale)
                    .translate(-centerX, -centerY)
            );
    }

    ticked(linkLabelGroups) {
        // Check if elements exist before updating (prevents errors during refresh)
        if (this.linkElements && this.linkElements.size && this.linkElements.size() > 0) {
            this.linkElements
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
        }

        // Position link labels with perpendicular offset to avoid overlap
        if (linkLabelGroups && linkLabelGroups.size && linkLabelGroups.size() > 0) {
            linkLabelGroups.attr('transform', d => {
                const midX = (d.source.x + d.target.x) / 2;
                const midY = (d.source.y + d.target.y) / 2;

                // Calculate perpendicular offset
                const dx = d.target.x - d.source.x;
                const dy = d.target.y - d.source.y;
                const len = Math.sqrt(dx * dx + dy * dy) || 1;

                // Perpendicular unit vector, offset by 12px
                const offsetX = (-dy / len) * 12;
                const offsetY = (dx / len) * 12;

                return `translate(${midX + offsetX}, ${midY + offsetY})`;
            });
        }

        if (this.nodeElements && this.nodeElements.size && this.nodeElements.size() > 0) {
            this.nodeElements
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);
        }

        if (this.labelElements && this.labelElements.size && this.labelElements.size() > 0) {
            this.labelElements
                .attr('x', d => d.x)
                .attr('y', d => d.y);
        }
    }

    drag() {
        return d3.drag()
            .on('start', (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            })
            .on('drag', (event, d) => {
                d.fx = event.x;
                d.fy = event.y;
            })
            .on('end', (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            });
    }

    onNodeClick(event, d) {
        this.selectedNode = d;

        // Highlight the clicked node
        this.nodeElements
            .attr('stroke', node => node.id === d.id ? '#667eea' : '#fff')
            .attr('stroke-width', node => node.id === d.id ? 4 : 2);

        // Show node info
        const nodeInfo = document.getElementById('nodeInfo');
        const nodeInfoTitle = document.getElementById('nodeInfoTitle');
        const nodeInfoDesc = document.getElementById('nodeInfoDesc');

        if (nodeInfo && nodeInfoTitle && nodeInfoDesc) {
            const nodeTypeInfo = this.nodeTypeMap.get(d.type);
            const typeLabel = nodeTypeInfo ? nodeTypeInfo.label : d.type;
            
            nodeInfoTitle.textContent = d.label || d.id;
            
            // 构建详细信息
            let infoText = `类型: ${typeLabel} | 连接数: ${d.degree}`;
            if (d.description) {
                infoText += `\n\n${d.description}`;
            }
            if (d.properties && Object.keys(d.properties).length > 0) {
                const propsText = Object.entries(d.properties)
                    .filter(([k, v]) => k !== 'description')
                    .map(([k, v]) => `${k}: ${v}`)
                    .join(' | ');
                if (propsText) {
                    infoText += `\n\n属性: ${propsText}`;
                }
            }
            
            nodeInfoDesc.textContent = infoText;
            nodeInfo.style.display = 'block';
        }

        // Emit custom event for other components
        window.dispatchEvent(new CustomEvent('nodeSelected', { detail: d }));
    }

    onNodeHover(event, d, isHover) {
        if (isHover) {
            // Highlight connected nodes and links
            const connectedNodeIds = new Set([d.id]);
            this.links.forEach(link => {
                if (link.source.id === d.id) connectedNodeIds.add(link.target.id);
                if (link.target.id === d.id) connectedNodeIds.add(link.source.id);
            });

            this.nodeElements
                .attr('opacity', node => connectedNodeIds.has(node.id) ? 1 : 0.3);

            this.linkElements
                .attr('opacity', link =>
                    link.source.id === d.id || link.target.id === d.id ? 1 : 0.1);

            this.labelElements
                .attr('opacity', node => connectedNodeIds.has(node.id) ? 1 : 0.3);
        } else {
            // Reset opacity
            this.nodeElements.attr('opacity', 1);
            this.linkElements.attr('opacity', 0.6);
            this.labelElements.attr('opacity', 1);
        }
    }

    searchNodes(query) {
        if (!query) {
            this.nodeElements.attr('opacity', 1);
            this.labelElements.attr('opacity', 1);
            return;
        }

        const lowerQuery = query.toLowerCase();
        const matchedIds = new Set();

        this.nodes.forEach(node => {
            if (node.label.toLowerCase().includes(lowerQuery) ||
                node.description.toLowerCase().includes(lowerQuery)) {
                matchedIds.add(node.id);
            }
        });

        this.nodeElements
            .attr('opacity', node => matchedIds.has(node.id) ? 1 : 0.2)
            .attr('stroke', node => matchedIds.has(node.id) ? '#667eea' : '#fff')
            .attr('stroke-width', node => matchedIds.has(node.id) ? 3 : 2);

        this.labelElements
            .attr('opacity', node => matchedIds.has(node.id) ? 1 : 0.2);

        // Center on first matched node
        if (matchedIds.size > 0) {
            const firstMatch = this.nodes.find(n => matchedIds.has(n.id));
            if (firstMatch && firstMatch.x && firstMatch.y) {
                this.centerOnNode(firstMatch);
            }
        }
    }

    centerOnNode(node) {
        const container = document.getElementById(this.containerId);
        const width = container.clientWidth;
        const height = container.clientHeight;

        this.svg.transition()
            .duration(750)
            .call(
                this.zoom.transform,
                d3.zoomIdentity
                    .translate(width / 2, height / 2)
                    .scale(1.5)
                    .translate(-node.x, -node.y)
            );
    }

    resetZoom() {
        const container = document.getElementById(this.containerId);
        const width = container.clientWidth;
        const height = container.clientHeight;

        this.svg.transition()
            .duration(750)
            .call(
                this.zoom.transform,
                d3.zoomIdentity.translate(0, 0).scale(1)
            );
    }

    // Clear all graph data and elements
    clear() {
        // Stop simulation completely and remove all event listeners FIRST
        if (this.simulation) {
            // Remove tick handler before stopping to prevent errors
            this.simulation.on('tick', null);
            // Stop the simulation
            this.simulation.stop();
            // Clear nodes and links from simulation
            this.simulation.nodes([]);
            const linkForce = this.simulation.force('link');
            if (linkForce) {
                linkForce.links([]);
            }
        }

        // Clear data arrays
        this.nodes = [];
        this.links = [];

        // Reset element references BEFORE removing DOM elements
        // This prevents tick handlers from trying to update null references
        this.nodeElements = null;
        this.linkElements = null;
        this.labelElements = null;
        this.selectedNode = null;

        // Remove all SVG elements in the group - more thorough cleanup
        if (this.g) {
            // Remove all child elements
            this.g.selectAll('*').remove();
            // Also clear any lingering elements by selecting all possible types
            this.g.selectAll('g.links').remove();
            this.g.selectAll('g.nodes').remove();
            this.g.selectAll('g.labels').remove();
            this.g.selectAll('g.link-labels').remove();
            this.g.selectAll('line.link').remove();
            this.g.selectAll('circle.node').remove();
            this.g.selectAll('text.node-label').remove();
            this.g.selectAll('text.link-label').remove();
        }

        // Also clear the entire SVG if it exists
        if (this.svg) {
            this.svg.selectAll('g').selectAll('*').remove();
        }

        console.log('Graph cleared');
    }

    // Refresh graph - clear and reload
    async refresh() {
        console.log('Starting graph refresh...');
        
        // Clear everything first
        this.clear();

        // Wait a bit to ensure DOM updates are complete
        await new Promise(resolve => setTimeout(resolve, 100));

        // Re-initialize simulation with completely fresh state
        if (this.simulation) {
            this.simulation.stop();
            // Remove all event listeners
            this.simulation.on('tick', null);
            // Reset nodes and links
            this.simulation.nodes([]);
            const linkForce = this.simulation.force('link');
            if (linkForce) {
                linkForce.links([]);
            }
        }

        // Now load new graph data
        return await this.loadGraph();
    }

    // Toggle fullscreen mode
    toggleFullscreen() {
        const container = document.getElementById(this.containerId);
        const card = container?.closest('.card');

        if (!card) return;

        const isFullscreen = card.classList.contains('fullscreen');

        if (isFullscreen) {
            // Exit fullscreen
            card.classList.remove('fullscreen');
            document.body.style.overflow = '';
        } else {
            // Enter fullscreen
            card.classList.add('fullscreen');
            document.body.style.overflow = 'hidden';
        }

        // Update dimensions and re-render
        setTimeout(() => {
            const newWidth = container.clientWidth;
            const newHeight = container.clientHeight;

            this.width = newWidth;
            this.height = newHeight;

            this.svg.attr('viewBox', [0, 0, newWidth, newHeight]);

            // Update force center
            if (this.simulation) {
                this.simulation.force('center', d3.forceCenter(newWidth / 2, newHeight / 2));
                this.simulation.force('x', d3.forceX(newWidth / 2).strength(0.05));
                this.simulation.force('y', d3.forceY(newHeight / 2).strength(0.05));
                this.simulation.alpha(0.3).restart();
            }

            // Fit to view after a short delay
            setTimeout(() => this.fitToView(), 500);
        }, 100);

        return !isFullscreen;
    }

    isFullscreen() {
        const container = document.getElementById(this.containerId);
        const card = container?.closest('.card');
        return card?.classList.contains('fullscreen') || false;
    }

    show() {
        const placeholder = document.getElementById('graphPlaceholder');
        const svgElement = document.getElementById(this.svgId);
        const controls = document.getElementById('graphControls');
        const legend = document.getElementById('graphLegend');

        if (placeholder) placeholder.style.display = 'none';
        if (svgElement) svgElement.style.display = 'block';
        if (controls) controls.style.display = 'flex';
        if (legend) legend.style.display = 'flex';
    }

    hide() {
        const placeholder = document.getElementById('graphPlaceholder');
        const svgElement = document.getElementById(this.svgId);
        const controls = document.getElementById('graphControls');
        const legend = document.getElementById('graphLegend');
        const nodeInfo = document.getElementById('nodeInfo');

        if (placeholder) placeholder.style.display = 'flex';
        if (svgElement) svgElement.style.display = 'none';
        if (controls) controls.style.display = 'none';
        if (legend) legend.style.display = 'none';
        if (nodeInfo) nodeInfo.style.display = 'none';
    }

    getNodeCount() {
        return this.nodes.length;
    }

    getLinkCount() {
        return this.links.length;
    }

    setData(nodes, edges) {
        /**
         * 直接设置图谱数据并渲染
         * 用于从外部加载特定文档的图谱
         */
        const data = {
            nodes: nodes || [],
            edges: edges || []
        };

        console.log(`Setting graph data: ${data.nodes.length} nodes, ${data.edges.length} edges`);

        this.processGraphData(data);
        this.render();
    }
}

// Export for use in other modules
window.KnowledgeGraph = KnowledgeGraph;
