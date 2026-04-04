'use client';

import * as React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Activity, Server, Cpu, Database, RefreshCw, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';

interface ServiceStatus {
  name: string;
  port: number;
  status: 'healthy' | 'unhealthy' | 'unknown';
  latency?: number;
  lastCheck?: string;
}

const mockServices: ServiceStatus[] = [
  { name: 'mock', port: 8001, status: 'healthy', latency: 12, lastCheck: new Date().toISOString() },
  { name: 'rules', port: 8002, status: 'healthy', latency: 8, lastCheck: new Date().toISOString() },
  { name: 'insight', port: 8003, status: 'healthy', latency: 15, lastCheck: new Date().toISOString() },
  { name: 'audit', port: 8004, status: 'healthy', latency: 10, lastCheck: new Date().toISOString() },
];

function StatusIndicator({ status }: { status: ServiceStatus['status'] }) {
  if (status === 'healthy') {
    return <CheckCircle className="h-5 w-5 text-green-500" />;
  } else if (status === 'unhealthy') {
    return <XCircle className="h-5 w-5 text-red-500" />;
  }
  return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
}

function ServiceCard({ service }: { service: ServiceStatus }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium">{service.name}</CardTitle>
        <StatusIndicator status={service.status} />
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-muted-foreground">Port: {service.port}</p>
            {service.latency && (
              <p className="text-xs text-muted-foreground">Latency: {service.latency}ms</p>
            )}
          </div>
          <Badge variant={service.status === 'healthy' ? 'success' : service.status === 'unhealthy' ? 'destructive' : 'secondary'}>
            {service.status}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}

export default function MonitorPage() {
  const [services, setServices] = React.useState<ServiceStatus[]>(mockServices);
  const [loading, setLoading] = React.useState(false);

  const handleRefresh = async () => {
    setLoading(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    setServices(mockServices);
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">System Monitor</h1>
          <p className="text-muted-foreground">Monitor service health and system metrics</p>
        </div>
        <Button variant="outline" onClick={handleRefresh} disabled={loading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Service Health */}
      <div>
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Server className="h-5 w-5" />
          Service Health
        </h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {services.map((service) => (
            <ServiceCard key={service.name} service={service} />
          ))}
        </div>
      </div>

      {/* System Metrics */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Cpu className="h-5 w-5" />
              Processing Metrics
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Events Processed (24h)</span>
                <span className="font-medium">1,234,567</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Processing Rate</span>
                <span className="font-medium">1,234 events/s</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Avg Processing Time</span>
                <span className="font-medium">12ms</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Error Rate</span>
                <span className="font-medium text-green-600">0.01%</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5" />
              Data Storage
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">PostgreSQL</span>
                <Badge variant="success">Connected</Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Redis</span>
                <Badge variant="success">Connected</Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Pulsar</span>
                <Badge variant="success">Connected</Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">ClickHouse</span>
                <Badge variant="secondary">Not Configured</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Stream Processing Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Stream Processing Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div>
              <p className="text-sm text-muted-foreground">Job Status</p>
              <p className="text-2xl font-bold text-green-600">Running</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Last Checkpoint</p>
              <p className="text-2xl font-bold">2 min ago</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Processed Records</p>
              <p className="text-2xl font-bold">1.2M</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Partition Lag</p>
              <p className="text-2xl font-bold">0</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
