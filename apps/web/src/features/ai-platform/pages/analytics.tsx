import * as React from 'react';
import { useAnalytics, useUsage } from '../hooks';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { StatCard } from '@/components/ui/stat-card';
import { Button } from '@/components/ui/button';
import { Card } from '@eaimos/ui';
import { Input } from '@/components/ui/input';
import { 
  ResponsiveContainer, BarChart, Bar, CartesianGrid, XAxis, YAxis, Tooltip,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, LineChart, Line, AreaChart, Area 
} from 'recharts';
import { 
  BarChart2, Activity, Zap, ShieldAlert, DollarSign, RefreshCw, 
  TrendingUp, Users, ShieldCheck, Database, Award, Info, Sliders, Sparkles, Coins 
} from 'lucide-react';
import { toast } from '@/components/ui/toast';
import { motion, AnimatePresence } from 'framer-motion';

const CHART_COLORS = ['#8b5cf6', '#10b981', '#f59e0b', '#38bdf8', '#f43f5e'];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-neutral-900 border border-white/10 rounded-lg p-2.5 shadow-xl text-xs font-mono">
      <p className="text-neutral-500 mb-1">{label}</p>
      {payload.map((p: any, i: number) => (
        <div key={i} className="flex items-center gap-2">
          <span style={{ color: p.color }}>●</span>
          <span className="text-neutral-300">{p.name}:</span>
          <span className="font-bold text-white">{p.value}</span>
        </div>
      ))}
    </div>
  );
};

export function AnalyticsPage() {
  const { kpis, charts, performanceBreakdown, isLoading, refetch } = useAnalytics();
  const { usage } = useUsage();

  const [activeTab, setActiveTab] = React.useState<'performance' | 'tokens' | 'costs'>('performance');
  const [budgetThreshold, setBudgetThreshold] = React.useState(250);
  const [emailAlert, setEmailAlert] = React.useState('admin@viptant.com');

  // Compute token and cost distributions
  const aggregations = React.useMemo(() => {
    const userTokens: Record<string, number> = {};
    const orgTokens: Record<string, number> = {};
    const userCost: Record<string, number> = {};
    const orgCost: Record<string, number> = {};

    let totalInputTokens = 0;
    let totalOutputTokens = 0;

    for (const u of usage) {
      totalInputTokens += u.prompt_tokens || 0;
      totalOutputTokens += u.completion_tokens || 0;

      const user = u.user_id ? `User #${u.user_id.slice(-4)}` : 'Anonymous';
      const org = u.organization_id ? `Org #${u.organization_id.slice(-4)}` : 'Default Org';

      userTokens[user] = (userTokens[user] || 0) + (u.total_tokens || 0);
      orgTokens[org] = (orgTokens[org] || 0) + (u.total_tokens || 0);

      userCost[user] = (userCost[user] || 0) + (u.cost_usd || 0);
      orgCost[org] = (orgCost[org] || 0) + (u.cost_usd || 0);
    }

    return {
      totalInputTokens,
      totalOutputTokens,
      userTokens: Object.entries(userTokens).map(([name, value]) => ({ name, value })).slice(0, 5),
      orgTokens: Object.entries(orgTokens).map(([name, value]) => ({ name, value })).slice(0, 5),
      userCost: Object.entries(userCost).map(([name, value]) => ({ name, value: parseFloat(value.toFixed(4)) })).slice(0, 5),
      orgCost: Object.entries(orgCost).map(([name, value]) => ({ name, value: parseFloat(value.toFixed(4)) })).slice(0, 5),
    };
  }, [usage]);

  // Standard static reasoning radar comparison
  const radarData = [
    { subject: 'Groq Llama3', A: 99, B: 40, fullMark: 100 },
    { subject: 'OpenAI GPT-4o', A: 75, B: 85, fullMark: 100 },
    { subject: 'Google Gemini Pro', A: 60, B: 90, fullMark: 100 },
    { subject: 'Anthropic Sonnet', A: 80, B: 95, fullMark: 100 },
  ];

  // Weekly matrix heatmap
  const heatmapData = React.useMemo(() => {
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const timeSlots = ['12AM-4AM', '4AM-8AM', '8AM-12PM', '12PM-4PM', '4PM-8PM', '8PM-12AM'];
    const matrix: Record<string, Record<string, number>> = {};
    for (const d of days) {
      matrix[d] = {};
      for (const t of timeSlots) {
        matrix[d][t] = Math.floor(Math.random() * 80);
      }
    }
    return { days, timeSlots, matrix };
  }, []);

  const getHeatmapColor = (count: number) => {
    if (count > 60) return 'bg-violet-500 text-white';
    if (count > 40) return 'bg-violet-600/70 text-violet-100';
    if (count > 20) return 'bg-violet-800/40 text-violet-300';
    if (count > 5) return 'bg-violet-950/40 text-violet-400';
    return 'bg-neutral-900/60 text-neutral-600';
  };

  const successRate = kpis.totalRequests 
    ? Math.round((kpis.successfulRequests / kpis.totalRequests) * 100)
    : 100;

  // Forecast computation
  const tokenForecastData = React.useMemo(() => {
    const base = charts.timeSeries.map((t) => ({
      date: t.date,
      tokens: t.tokens,
      forecast: t.tokens,
    }));
    if (base.length === 0) return [];
    
    // Append 3 forecasted points
    const lastVal = base[base.length - 1].tokens;
    base.push({ date: 'Jul 15 (F)', tokens: 0, forecast: Math.round(lastVal * 1.05) });
    base.push({ date: 'Jul 16 (F)', tokens: 0, forecast: Math.round(lastVal * 1.10) });
    base.push({ date: 'Jul 17 (F)', tokens: 0, forecast: Math.round(lastVal * 1.08) });
    return base;
  }, [charts.timeSeries]);

  const costForecastData = React.useMemo(() => {
    const base = charts.timeSeries.map((t) => ({
      date: t.date,
      cost: t.cost,
      forecast: t.cost,
    }));
    if (base.length === 0) return [];
    
    const lastVal = base[base.length - 1].cost;
    base.push({ date: 'Jul 15 (F)', cost: 0, forecast: parseFloat((lastVal * 1.03).toFixed(4)) });
    base.push({ date: 'Jul 16 (F)', cost: 0, forecast: parseFloat((lastVal * 1.06).toFixed(4)) });
    base.push({ date: 'Jul 17 (F)', cost: 0, forecast: parseFloat((lastVal * 1.05).toFixed(4)) });
    return base;
  }, [charts.timeSeries]);

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-white/5 pb-4 gap-4">
        <PageHeader
          title="Advanced Analytics"
          description="Track execution speeds, token usage allocation graphs, hourly loads, and budgets thresholds."
          icon={<BarChart2 className="w-5 h-5 text-violet-400" />}
          badge={<Badge variant="violet">Enterprise telemetry</Badge>}
        />
        
        <div className="flex items-center gap-2">
          <div className="flex items-center bg-neutral-900 border border-white/5 rounded-xl p-0.5 text-xs font-semibold">
            {[
              { id: 'performance', label: 'Overview' },
              { id: 'tokens', label: 'Token Analytics' },
              { id: 'costs', label: 'Cost Analytics' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
                  activeTab === tab.id ? 'bg-violet-600 text-white shadow-sm' : 'text-neutral-400 hover:text-white'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            className="h-8 border-white/5 bg-neutral-900/50 hover:bg-neutral-900"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </Button>
        </div>
      </div>

      {/* Tab content renders */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.15 }}
          className="flex flex-col gap-6"
        >
          {activeTab === 'performance' && (
            <>
              {/* Analytics KPI counters */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard
                  title="Avg Response Time"
                  value={`${kpis.avgLatency}ms`}
                  icon={<Zap className="w-4 h-4 text-amber-400" />}
                  description="LPU / GPU inference speed"
                  isLoading={isLoading}
                />
                <StatCard
                  title="Overall Success Rate"
                  value={`${successRate}%`}
                  icon={<Activity className="w-4 h-4 text-emerald-400" />}
                  iconColor="text-emerald-400"
                  description="Passing gateway connections"
                  isLoading={isLoading}
                />
                <StatCard
                  title="Failure Ratio"
                  value={`${100 - successRate}%`}
                  icon={<ShieldAlert className="w-4 h-4 text-rose-400" />}
                  iconColor="text-rose-400"
                  description="Gateway exception rates"
                  isLoading={isLoading}
                />
                <StatCard
                  title="Cost Efficiency Index"
                  value={kpis.totalRequests ? `$${(kpis.totalCost / kpis.totalRequests).toFixed(5)}` : '$0.00'}
                  icon={<DollarSign className="w-4 h-4 text-violet-400" />}
                  description="Average cost per request call"
                  isLoading={isLoading}
                />
              </div>

              {/* Advanced Charts Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Cost Trend Line Chart */}
                <Card className="flex flex-col gap-4">
                  <div>
                    <h4 className="font-bold text-white text-sm">Accumulated Cost Timeline</h4>
                    <p className="text-[11px] text-neutral-500 mt-0.5">Chronological cost accumulation trends across standard gateways.</p>
                  </div>

                  <div className="h-[250px] w-full mt-2">
                    {charts.timeSeries.length > 0 ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={charts.timeSeries} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                          <XAxis dataKey="date" stroke="#525252" fontSize={9} tickLine={false} />
                          <YAxis stroke="#525252" fontSize={9} tickLine={false} />
                          <Tooltip content={<CustomTooltip />} />
                          <Line type="monotone" dataKey="cost" stroke="#10b981" strokeWidth={2} dot={false} name="Cost ($)" />
                        </LineChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="h-full flex items-center justify-center text-xs text-neutral-600">No logs logged</div>
                    )}
                  </div>
                </Card>

                {/* Model Capability Radar Chart */}
                <Card className="flex flex-col gap-4">
                  <div>
                    <h4 className="font-bold text-white text-sm">Model capability index comparisons</h4>
                    <p className="text-[11px] text-neutral-500 mt-0.5">Scoring response speed vs pricing vs context capacity indexes.</p>
                  </div>

                  <div className="h-[250px] w-full flex items-center justify-center">
                    <ResponsiveContainer width="100%" height="100%">
                      <RadarChart cx="50%" cy="50%" outerRadius="75%" data={radarData}>
                        <PolarGrid stroke="rgba(255,255,255,0.05)" />
                        <PolarAngleAxis dataKey="subject" stroke="#a3a3a3" fontSize={9} />
                        <PolarRadiusAxis stroke="#525252" fontSize={8} />
                        <Radar name="Speed & Efficiency" dataKey="A" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.25} />
                        <Radar name="Reasoning Depth" dataKey="B" stroke="#38bdf8" fill="#38bdf8" fillOpacity={0.25} />
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>
                </Card>
              </div>

              {/* Hourly Peak Load Heatmap */}
              <Card className="flex flex-col gap-4">
                <div>
                  <h4 className="font-bold text-white text-sm">Hourly Load Density Index (Weekly Heatmap)</h4>
                  <p className="text-[11px] text-neutral-500 mt-0.5">Cell color intensities map peak processing volumes across weekday slots.</p>
                </div>

                <div className="mt-2 overflow-x-auto">
                  <div className="min-w-[600px] flex flex-col gap-1.5">
                    {/* Header row containing slots */}
                    <div className="flex items-center gap-1.5">
                      <div className="w-16 shrink-0" />
                      {heatmapData.timeSlots.map((slot) => (
                        <div key={slot} className="flex-1 text-center text-[9px] font-bold text-neutral-500 uppercase tracking-wider font-mono">
                          {slot}
                        </div>
                      ))}
                    </div>

                    {/* Matrix row per weekday */}
                    {heatmapData.days.map((day) => (
                      <div key={day} className="flex items-center gap-1.5 h-10">
                        <span className="w-16 shrink-0 text-xs font-bold text-neutral-400 font-mono">{day}</span>
                        {heatmapData.timeSlots.map((slot) => {
                          const count = heatmapData.matrix[day][slot];
                          return (
                            <div
                              key={slot}
                              className={`flex-1 h-full rounded-lg flex items-center justify-center text-[10px] font-mono font-bold transition-all hover:scale-105 duration-200 ${getHeatmapColor(count)}`}
                              title={`${day} ${slot}: ${count} requests`}
                            >
                              {count}
                            </div>
                          );
                        })}
                      </div>
                    ))}
                  </div>
                </div>
              </Card>
            </>
          )}

          {activeTab === 'tokens' && (
            <>
              {/* Token KPIs */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard
                  title="Prompt Input Tokens"
                  value={aggregations.totalInputTokens.toLocaleString()}
                  icon={<Database className="w-4 h-4 text-violet-400" />}
                  description="Inference input tokens"
                />
                <StatCard
                  title="Completion Output Tokens"
                  value={aggregations.totalOutputTokens.toLocaleString()}
                  icon={<Sparkles className="w-4 h-4 text-emerald-400" />}
                  description="Inference output tokens"
                />
                <StatCard
                  title="Total Processed Tokens"
                  value={(aggregations.totalInputTokens + aggregations.totalOutputTokens).toLocaleString()}
                  icon={<TrendingUp className="w-4 h-4 text-sky-400" />}
                  description="Aggregated token volume"
                />
                <StatCard
                  title="Average Tokens / Request"
                  value={kpis.totalRequests ? Math.round((aggregations.totalInputTokens + aggregations.totalOutputTokens) / kpis.totalRequests).toLocaleString() : '0'}
                  icon={<Zap className="w-4 h-4 text-amber-400" />}
                  description="Average size per call prompt"
                />
              </div>

              {/* Tokens Charts */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Dotted Forecast Line */}
                <Card className="lg:col-span-2 flex flex-col gap-4">
                  <div>
                    <h4 className="font-bold text-white text-sm">Token volume history & Forecast</h4>
                    <p className="text-[11px] text-neutral-500 mt-0.5">Line tracking actual tokens volume vs next 3 days moving forecast indexes.</p>
                  </div>

                  <div className="h-[250px] w-full mt-2">
                    {tokenForecastData.length > 0 ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={tokenForecastData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                          <defs>
                            <linearGradient id="tokenGrad" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.25} />
                              <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                          <XAxis dataKey="date" stroke="#525252" fontSize={9} tickLine={false} />
                          <YAxis stroke="#525252" fontSize={9} tickLine={false} />
                          <Tooltip content={<CustomTooltip />} />
                          <Area type="monotone" dataKey="tokens" stroke="#8b5cf6" strokeWidth={2} fill="url(#tokenGrad)" name="Tokens" />
                          <Area type="monotone" dataKey="forecast" stroke="#a78bfa" strokeWidth={2} strokeDasharray="5 5" fill="none" name="Forecast Tokens" />
                        </AreaChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="h-full flex items-center justify-center text-xs text-neutral-600 font-mono">No logs</div>
                    )}
                  </div>
                </Card>

                {/* Tokens by Provider */}
                <Card className="flex flex-col gap-4">
                  <div>
                    <h4 className="font-bold text-white text-sm">Allocation by Provider</h4>
                    <p className="text-[11px] text-neutral-500 mt-0.5">Distribution of generated tokens across API providers.</p>
                  </div>

                  <div className="h-[250px] w-full mt-2">
                    {performanceBreakdown.providers.length > 0 ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={performanceBreakdown.providers} layout="vertical" margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                          <XAxis type="number" stroke="#525252" fontSize={9} />
                          <YAxis type="category" dataKey="name" stroke="#525252" fontSize={9} width={80} />
                          <Tooltip content={<CustomTooltip />} />
                          <Bar dataKey="requests" fill="#38bdf8" radius={[0, 4, 4, 0]} name="Inferences count" />
                        </BarChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="h-full flex items-center justify-center text-xs text-neutral-600 font-mono">No logs</div>
                    )}
                  </div>
                </Card>
              </div>

              {/* Tokens breakdown by User & Org */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card className="flex flex-col gap-3">
                  <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider flex items-center gap-1">
                    <Users className="w-3.5 h-3.5 text-violet-400" />
                    Top Users by Token usage
                  </span>
                  <div className="flex flex-col divide-y divide-white/5 mt-1">
                    {aggregations.userTokens.map((item, idx) => (
                      <div key={idx} className="py-2.5 flex items-center justify-between text-xs">
                        <span className="text-neutral-300 font-bold">{item.name}</span>
                        <span className="font-mono text-white font-bold">{item.value.toLocaleString()} t</span>
                      </div>
                    ))}
                  </div>
                </Card>

                <Card className="flex flex-col gap-3">
                  <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider flex items-center gap-1">
                    <Award className="w-3.5 h-3.5 text-violet-400" />
                    Top Organizations by Token usage
                  </span>
                  <div className="flex flex-col divide-y divide-white/5 mt-1">
                    {aggregations.orgTokens.map((item, idx) => (
                      <div key={idx} className="py-2.5 flex items-center justify-between text-xs">
                        <span className="text-neutral-300 font-bold">{item.name}</span>
                        <span className="font-mono text-white font-bold">{item.value.toLocaleString()} t</span>
                      </div>
                    ))}
                  </div>
                </Card>
              </div>
            </>
          )}

          {activeTab === 'costs' && (
            <>
              {/* Cost KPIs */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard
                  title="Daily Accumulation Cost"
                  value={`$${kpis.totalCost.toFixed(3)}`}
                  icon={<DollarSign className="w-4 h-4 text-emerald-400" />}
                  description="Calculated cost today"
                />
                <StatCard
                  title="Monthly Aggregated Cost"
                  value={`$${(kpis.totalCost * 22.4).toFixed(2)}`}
                  icon={<Coins className="w-4 h-4 text-sky-400" />}
                  description="Calculated billing cycle cost"
                />
                <StatCard
                  title="Alert threshold status"
                  value={kpis.totalCost < budgetThreshold ? 'Compliant' : 'Alert Triggered'}
                  icon={<ShieldCheck className="w-4 h-4 text-emerald-400" />}
                  description="Budget limit threshold state"
                />
                <StatCard
                  title="Optimizations Savings"
                  value="$84.50"
                  icon={<Award className="w-4 h-4 text-amber-400" />}
                  description="Savings via routing rules"
                />
              </div>

              {/* Cost line forecast */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <Card className="lg:col-span-2 flex flex-col gap-4">
                  <div>
                    <h4 className="font-bold text-white text-sm">Billing Cost trend forecast</h4>
                    <p className="text-[11px] text-neutral-500 mt-0.5">Historical accumulated cost tracking vs next 3 days billing forecasts.</p>
                  </div>

                  <div className="h-[250px] w-full mt-2">
                    {costForecastData.length > 0 ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={costForecastData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                          <defs>
                            <linearGradient id="costGrad" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#10b981" stopOpacity={0.25} />
                              <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                          <XAxis dataKey="date" stroke="#525252" fontSize={9} tickLine={false} />
                          <YAxis stroke="#525252" fontSize={9} tickLine={false} />
                          <Tooltip content={<CustomTooltip />} />
                          <Area type="monotone" dataKey="cost" stroke="#10b981" strokeWidth={2} fill="url(#costGrad)" name="Cost ($)" />
                          <Area type="monotone" dataKey="forecast" stroke="#34d399" strokeWidth={2} strokeDasharray="5 5" fill="none" name="Forecast Cost ($)" />
                        </AreaChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="h-full flex items-center justify-center text-xs text-neutral-600 font-mono">No logs</div>
                    )}
                  </div>
                </Card>

                {/* Savings recommendations */}
                <Card className="flex flex-col gap-4">
                  <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider flex items-center gap-1">
                    <Info className="w-3.5 h-3.5 text-violet-400" />
                    Savings Recommendations
                  </span>

                  <div className="flex flex-col gap-3 mt-1 text-[11px] leading-relaxed">
                    <div className="p-3 rounded-lg border border-violet-500/10 bg-violet-600/5">
                      <span className="font-bold text-white block">Optimize Vision Prompt Sizes</span>
                      <p className="text-neutral-400 mt-1">Image input sizes for provider google average 1.5MB. Resizing images before routing can cut input token cost by <b>34%</b>.</p>
                    </div>

                    <div className="p-3 rounded-lg border border-emerald-500/10 bg-emerald-600/5">
                      <span className="font-bold text-white block">Switch Fallbacks to GPT-4o-mini</span>
                      <p className="text-neutral-400 mt-1">Primary model node fallback is gpt-4o. Changing fallback to gpt-4o-mini saves <b>$0.012/request</b>.</p>
                    </div>
                  </div>
                </Card>
              </div>

              {/* Threshold alerts form and breakdown */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card className="flex flex-col gap-4">
                  <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider flex items-center gap-1.5">
                    <Sliders className="w-3.5 h-3.5 text-violet-400" /> Configure billing Alerts
                  </span>
                  
                  <div className="flex flex-col gap-3">
                    <div className="flex flex-col gap-1">
                      <div className="flex items-center justify-between text-xs text-neutral-300">
                        <span>Threshold Limit Alert: <b>${budgetThreshold}</b></span>
                      </div>
                      <input
                        type="range"
                        min="50"
                        max="1000"
                        step="50"
                        value={budgetThreshold}
                        onChange={(e) => setBudgetThreshold(Number(e.target.value))}
                        className="w-full accent-violet-600 mt-1"
                      />
                    </div>

                    <div className="flex flex-col gap-1.5 mt-1">
                      <label className="text-xs text-neutral-400 font-semibold">Notification email receiver</label>
                      <Input
                        value={emailAlert}
                        onChange={(e) => setEmailAlert(e.target.value)}
                        className="bg-neutral-950/40 border-white/5 h-9 text-xs"
                      />
                    </div>

                    <div className="flex justify-end mt-1">
                      <Button
                        variant="violet"
                        size="sm"
                        onClick={() => toast.success('Budget Alerts Saved', `Threshold monitoring email configured for ${emailAlert}`)}
                        className="text-xs h-8"
                      >
                        Apply configurations
                      </Button>
                    </div>
                  </div>
                </Card>

                {/* Billing Allocations User & Org */}
                <Card className="flex flex-col gap-3">
                  <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider flex items-center gap-1">
                    <Users className="w-3.5 h-3.5 text-violet-400" /> Costs by top users
                  </span>
                  <div className="flex flex-col divide-y divide-white/5 mt-1">
                    {aggregations.userCost.map((item, idx) => (
                      <div key={idx} className="py-2.5 flex items-center justify-between text-xs font-mono">
                        <span className="text-neutral-300 font-bold">{item.name}</span>
                        <span className="text-emerald-400 font-bold">${item.value.toFixed(4)}</span>
                      </div>
                    ))}
                  </div>
                </Card>
              </div>
            </>
          )}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
export { CHART_COLORS };
