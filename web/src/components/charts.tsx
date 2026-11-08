"use client";

import { Bar, BarChart, CartesianGrid, Cell, LabelList, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const MUTED = "#8c8f88";
const GRID = "#e6e7e2";
const INK2 = "#5d6159";
export const SERIES = { A: "#3a6ff0", B: "#ff8a3d" } as const;

const tooltipStyle = {
  contentStyle: { borderRadius: 14, border: "none", fontSize: 12, boxShadow: "0 8px 24px rgba(14,15,12,.12)" },
  labelStyle: { color: "#0e0f0c", fontWeight: 600 },
  cursor: { fill: "rgba(0,0,0,0.04)" },
};

/** Single-series horizontal bars, sorted by value, with direct value labels. */
export function HBar({ data, format = (v: number) => String(v), color = SERIES.A, height = 220 }: {
  data: { name: string; value: number }[];
  format?: (v: number) => string;
  color?: string;
  height?: number;
}) {
  const sorted = [...data].sort((a, b) => b.value - a.value);
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={sorted} layout="vertical" margin={{ top: 4, right: 48, bottom: 4, left: 8 }} barCategoryGap={8}>
        <CartesianGrid horizontal={false} stroke={GRID} />
        <XAxis type="number" tick={{ fill: MUTED, fontSize: 11 }} axisLine={{ stroke: "#cfd1ca" }} tickLine={false} tickFormatter={format} />
        <YAxis type="category" dataKey="name" width={120} tick={{ fill: INK2, fontSize: 12 }} axisLine={false} tickLine={false} />
        <Tooltip {...tooltipStyle} formatter={(v) => [format(Number(v)), ""]} separator="" />
        <Bar dataKey="value" fill={color} radius={[0, 8, 8, 0]} maxBarSize={20} isAnimationActive={false}>
          <LabelList dataKey="value" position="right" formatter={(v) => format(Number(v))} style={{ fill: INK2, fontSize: 11 }} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

/** Path A vs Path B grouped vertical bars on one shared scale. */
export function PathBars({ data, format = (v: number) => String(v), height = 260, domain }: {
  data: { name: string; A?: number; B?: number }[];
  format?: (v: number) => string;
  height?: number;
  domain?: [number, number];
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 18, right: 8, bottom: 4, left: 0 }} barGap={2} barCategoryGap="22%">
        <CartesianGrid vertical={false} stroke={GRID} />
        <XAxis dataKey="name" tick={{ fill: INK2, fontSize: 11 }} axisLine={{ stroke: "#cfd1ca" }} tickLine={false} interval={0} />
        <YAxis tick={{ fill: MUTED, fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={format} width={44} domain={domain} />
        <Tooltip {...tooltipStyle} formatter={(v, n) => [format(Number(v)), `Path ${n}`]} />
        <Legend verticalAlign="top" align="right" height={24} iconType="circle" iconSize={8} formatter={(v) => <span style={{ color: INK2, fontSize: 12 }}>Path {v}</span>} />
        {(["A", "B"] as const).map((p) => (
          <Bar key={p} dataKey={p} fill={SERIES[p]} radius={[8, 8, 0, 0]} maxBarSize={22} isAnimationActive={false} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

/** Small vertical bars for a handful of categories (e.g. review states). */
export function ColumnBars({ data, height = 200 }: { data: { name: string; value: number; color: string }[]; height?: number }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 18, right: 8, bottom: 4, left: 0 }}>
        <CartesianGrid vertical={false} stroke={GRID} />
        <XAxis dataKey="name" tick={{ fill: INK2, fontSize: 11 }} axisLine={{ stroke: "#cfd1ca" }} tickLine={false} interval={0} />
        <YAxis allowDecimals={false} tick={{ fill: MUTED, fontSize: 11 }} axisLine={false} tickLine={false} width={32} />
        <Tooltip {...tooltipStyle} formatter={(v) => [String(v), ""]} separator="" />
        <Bar dataKey="value" radius={[8, 8, 0, 0]} maxBarSize={40} isAnimationActive={false}>
          {data.map((d) => (
            <Cell key={d.name} fill={d.color} />
          ))}
          <LabelList dataKey="value" position="top" style={{ fill: INK2, fontSize: 11 }} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
