import { colors, space } from "../styles";

interface CharacterGraphProps {
  characters: any[];
}

export default function CharacterGraph({ characters }: CharacterGraphProps) {
  if (characters.length === 0) {
    return <div style={{ color: colors.muted, textAlign: "center", padding: space[8] }}>暂无角色数据</div>;
  }
  const cx = 200, cy = 150, r = 120;
  const mainChar = characters[0];
  const others = characters.slice(1);
  return (
    <svg viewBox="0 0 400 300" width="100%" height="300">
      {others.map((_, i) => {
        const angle = (i / others.length) * 2 * Math.PI - Math.PI / 2;
        const x = cx + r * Math.cos(angle);
        const y = cy + r * Math.sin(angle);
        return <line key={i} x1={cx} y1={cy} x2={x} y2={y} stroke={colors.border} strokeWidth={2} />;
      })}
      <circle cx={cx} cy={cy} r={35} fill={colors.accentBg} stroke={colors.accent} strokeWidth={2} />
      <text x={cx} y={cy + 4} textAnchor="middle" fontSize={13} fill={colors.fg} fontWeight={600}>{mainChar.name}</text>
      {others.map((c, i) => {
        const angle = (i / others.length) * 2 * Math.PI - Math.PI / 2;
        const x = cx + r * Math.cos(angle);
        const y = cy + r * Math.sin(angle);
        return (
          <g key={i}>
            <circle cx={x} cy={y} r={25} fill={colors.surface} stroke={colors.border} strokeWidth={2} />
            <text x={x} y={y + 4} textAnchor="middle" fontSize={11} fill={colors.fgSecondary}>{c.name}</text>
          </g>
        );
      })}
    </svg>
  );
}
