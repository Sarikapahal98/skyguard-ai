import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

export default function TrendChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={data}>
        <XAxis dataKey="recorded_at" tickFormatter={(t) => new Date(t).toLocaleTimeString()} />
        <YAxis />
        <Tooltip labelFormatter={(t) => new Date(t).toLocaleTimeString()} />
        <Line type="monotone" dataKey="temperature" stroke="#2E86AB" dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}