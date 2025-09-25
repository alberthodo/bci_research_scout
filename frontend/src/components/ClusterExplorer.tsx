import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import type { ClusterData, ClusterPoint } from '../types';

interface ClusterExplorerProps {
  data: ClusterData;
  className?: string;
}

const ClusterExplorer: React.FC<ClusterExplorerProps> = ({ 
  data, 
  className = '' 
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [selectedCluster, setSelectedCluster] = useState<number | null>(null);
  const [hoveredPoint, setHoveredPoint] = useState<ClusterPoint | null>(null);
  const [, setShowTooltip] = useState(false);
  const [, setTooltipPosition] = useState({ x: 0, y: 0 });

  const colors = [
    '#ef4444', '#22c55e', '#a855f7', '#f59e0b', '#ec4899',
    '#0ea5e9', '#10b981', '#f97316', '#8b5cf6', '#06b6d4'
  ];

  useEffect(() => {
    if (!data.points.length || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = 800;
    const height = 600;
    const margin = { top: 20, right: 20, bottom: 20, left: 20 };

    // Set up scales
    const xExtent = d3.extent(data.points, d => d.x) as [number, number];
    const yExtent = d3.extent(data.points, d => d.y) as [number, number];
    
    const xScale = d3.scaleLinear()
      .domain(xExtent)
      .range([margin.left, width - margin.right]);
    
    const yScale = d3.scaleLinear()
      .domain(yExtent)
      .range([height - margin.bottom, margin.top]);

    // Create tooltip
    const tooltip = d3.select('body').append('div')
      .attr('class', 'cluster-tooltip')
      .style('position', 'absolute')
      .style('background', 'rgba(0, 0, 0, 0.8)')
      .style('color', 'white')
      .style('padding', '8px')
      .style('border-radius', '4px')
      .style('font-size', '12px')
      .style('pointer-events', 'none')
      .style('opacity', 0)
      .style('z-index', 1000);

    // Draw points
    svg.selectAll('circle')
      .data(data.points)
      .enter()
      .append('circle')
      .attr('cx', d => xScale(d.x))
      .attr('cy', d => yScale(d.y))
      .attr('r', d => {
        const baseRadius = 4;
        const citationBonus = d.citation_count ? Math.min(d.citation_count / 100, 3) : 0;
        return baseRadius + citationBonus;
      })
      .attr('fill', d => {
        const opacity = selectedCluster === null || selectedCluster === d.cluster_id ? 0.7 : 0.2;
        return colors[d.cluster_id % colors.length] + Math.floor(opacity * 255).toString(16).padStart(2, '0');
      })
      .attr('stroke', d => colors[d.cluster_id % colors.length])
      .attr('stroke-width', 1)
      .style('cursor', 'pointer')
      .on('mouseover', function(event, d) {
        setHoveredPoint(d);
        setShowTooltip(true);
        
        const [x, y] = d3.pointer(event, document.body);
        setTooltipPosition({ x, y });
        
        tooltip.transition().duration(200).style('opacity', 0.9);
        tooltip.html(`
          <div><strong>${d.title}</strong></div>
          <div>Year: ${d.year}</div>
          <div>Cluster: ${d.cluster_id}</div>
          <div>Keywords: ${d.keywords.slice(0, 3).join(', ')}</div>
          ${d.citation_count ? `<div>Citations: ${d.citation_count}</div>` : ''}
        `)
        .style('left', (x + 10) + 'px')
        .style('top', (y - 10) + 'px');
      })
      .on('mouseout', function() {
        setHoveredPoint(null);
        setShowTooltip(false);
        tooltip.transition().duration(200).style('opacity', 0);
      })
      .on('click', function(_, d) {
        setSelectedCluster(selectedCluster === d.cluster_id ? null : d.cluster_id);
      });

    // Add cluster labels
    const clusterCenters = Object.keys(data.clusters).map(clusterId => {
      const clusterPoints = data.points.filter(p => p.cluster_id === parseInt(clusterId));
      const centerX = d3.mean(clusterPoints, p => p.x) || 0;
      const centerY = d3.mean(clusterPoints, p => p.y) || 0;
      return {
        id: parseInt(clusterId),
        x: centerX,
        y: centerY,
        size: clusterPoints.length
      };
    });

    svg.selectAll('.cluster-label')
      .data(clusterCenters)
      .enter()
      .append('text')
      .attr('class', 'cluster-label')
      .attr('x', d => xScale(d.x))
      .attr('y', d => yScale(d.y))
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .style('font-size', '12px')
      .style('font-weight', 'bold')
      .style('fill', d => colors[d.id % colors.length])
      .style('pointer-events', 'none')
      .text(d => `C${d.id}`);

    return () => {
      tooltip.remove();
    };
  }, [data, selectedCluster]);

  const selectedClusterData = selectedCluster !== null ? data.clusters[selectedCluster] : null;

  // Show message if there's insufficient data
  if (data.message) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border p-6 ${className}`}>
        <div className="text-center py-8">
          <div className="text-gray-400 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Insufficient Data for Clustering</h3>
          <p className="text-gray-500">{data.message}</p>
          <p className="text-sm text-gray-400 mt-2">
            Try adding more BCI papers to the database to enable clustering visualization.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-sm border p-6 ${className}`}>
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Paper Clusters</h3>
          <div className="text-sm text-gray-500">
            Algorithm: {data.algorithm} • {data.points.length} papers
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          {Object.entries(data.clusters).map(([clusterId, cluster]) => (
            <div
              key={clusterId}
              className={`p-3 rounded-lg border-2 cursor-pointer transition-colors ${
                selectedCluster === parseInt(clusterId)
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => setSelectedCluster(
                selectedCluster === parseInt(clusterId) ? null : parseInt(clusterId)
              )}
            >
              <div className="flex items-center space-x-2 mb-2">
                <div
                  className="w-4 h-4 rounded-full"
                  style={{ backgroundColor: colors[parseInt(clusterId) % colors.length] }}
                />
                <span className="font-medium text-sm">Cluster {clusterId}</span>
              </div>
              <div className="text-xs text-gray-600">
                {cluster.size} papers
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {cluster.year_range.min}-{cluster.year_range.max}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="relative">
        <svg
          ref={svgRef}
          width="100%"
          height="600"
          className="border rounded-lg bg-gray-50"
        />
        
        {hoveredPoint && (
          <div className="absolute top-4 right-4 bg-white p-3 rounded-lg shadow-lg border max-w-xs">
            <h4 className="font-medium text-sm mb-2">{hoveredPoint.title}</h4>
            <div className="text-xs text-gray-600 space-y-1">
              <div>Year: {hoveredPoint.year}</div>
              <div>Cluster: {hoveredPoint.cluster_id}</div>
              <div>Keywords: {hoveredPoint.keywords.slice(0, 3).join(', ')}</div>
              {hoveredPoint.citation_count && (
                <div>Citations: {hoveredPoint.citation_count}</div>
              )}
            </div>
          </div>
        )}
      </div>

      {selectedClusterData && (
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <h4 className="font-medium text-gray-900 mb-3">
            Cluster {selectedCluster} Details
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-gray-600 mb-2">Top Keywords:</div>
              <div className="flex flex-wrap gap-1">
                {selectedClusterData.top_keywords.map((keyword) => (
                  <span
                    key={keyword}
                    className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded-full"
                  >
                    {keyword}
                  </span>
                ))}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600 mb-2">Statistics:</div>
              <div className="text-sm space-y-1">
                <div>Papers: {selectedClusterData.size}</div>
                <div>Year Range: {selectedClusterData.year_range.min} - {selectedClusterData.year_range.max}</div>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="mt-4 text-xs text-gray-500">
        <p>• Click on points to see details</p>
        <p>• Click on cluster boxes to filter</p>
        <p>• Circle size indicates citation count</p>
      </div>
    </div>
  );
};

export default ClusterExplorer;
