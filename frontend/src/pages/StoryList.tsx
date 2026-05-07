import { useState, CSSProperties } from "react";
import { Link } from "react-router-dom";
import { api, StoryListItem } from "../services/api";
import { useApi } from "../hooks/useApi";
import LoadingSpinner from "../components/LoadingSpinner";
import { colors, space, font, bp, shadows, radius, genreColors, btn, layout } from "../styles";

const styles: Record<string, React.CSSProperties> = {
  pageHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: space[6],
  },
  headerLeft: {
    display: "flex",
    flexDirection: "column",
    gap: space[1],
  },
  pageTitle: {
    fontFamily: "'Noto Serif SC','Songti SC','STSong',Georgia,serif",
    fontSize: "28px",
    fontWeight: 700,
    color: colors.fg,
    letterSpacing: "-0.02em",
  },
  pageSubtitle: {
    fontSize: "14px",
    color: colors.muted,
  },
  createBtn: {
    display: "inline-flex",
    alignItems: "center",
    gap: space[2],
    padding: `${space[2]} ${space[5]}`,
    fontSize: "14px",
    fontWeight: 600,
    fontFamily: "inherit",
    background: colors.primary,
    color: "#fff",
    border: "none",
    borderRadius: radius.md,
    cursor: "pointer",
    textDecoration: "none",
    transition: "all 0.15s ease",
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
    gap: "20px",
  },
  card: {
    background: colors.surfaceRaised,
    border: `1px solid ${colors.border}`,
    borderRadius: radius.md,
    overflow: "hidden",
    cursor: "pointer",
    textDecoration: "none",
    color: colors.fg,
    transition: "box-shadow 0.2s ease, border-color 0.15s, transform 0.2s ease",
  },
  cardHover: {
    boxShadow: shadows.hover,
    borderColor: colors.mutedLight,
    transform: "translateY(-2px)",
  },
  genreStrip: {
    height: "4px",
    width: "100%",
  },
  cardBody: {
    padding: "20px 22px",
  },
  cardTitle: {
    fontFamily: "'Noto Serif SC','Songti SC','STSong',Georgia,serif",
    fontSize: "18px",
    fontWeight: 600,
    color: colors.fg,
    marginBottom: "6px",
    letterSpacing: "-0.01em",
  },
  cardTheme: {
    fontSize: "13px",
    color: colors.muted,
    display: "-webkit-box",
    WebkitLineClamp: 2,
    WebkitBoxOrient: "vertical",
    overflow: "hidden",
    marginBottom: "16px",
    lineHeight: 1.5,
  },
  cardMeta: {
    display: "flex",
    gap: "12px",
    alignItems: "center",
    marginBottom: "14px",
  },
  cardBadge: {
    fontSize: "11px",
    fontWeight: 500,
    padding: "2px 8px",
    borderRadius: "20px",
    background: colors.bgWarm,
    color: colors.fgSecondary,
  },
  cardStat: {
    fontSize: "12px",
    color: colors.muted,
  },
  cardProgress: {
    height: "3px",
    background: colors.borderLight,
    borderRadius: "2px",
    overflow: "hidden",
  },
  cardProgressBar: {
    height: "100%",
    borderRadius: "2px",
    transition: "width 0.3s ease",
  },
  cardFooter: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "12px 22px",
    borderTop: `1px solid ${colors.borderLight}`,
    fontSize: "12px",
    color: colors.muted,
  },
  deleteBtn: {
    padding: "4px 10px",
    fontSize: "12px",
    fontWeight: 500,
    fontFamily: "inherit",
    background: "transparent",
    color: colors.muted,
    border: `1px solid ${colors.border}`,
    borderRadius: "6px",
    cursor: "pointer",
    transition: "all 0.15s ease",
  },
  deleteBtnHover: {
    background: colors.dangerMuted,
    color: colors.danger,
    borderColor: colors.dangerBorder,
  },
  emptyContainer: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    padding: `${space[16]} ${space[6]}`,
    textAlign: "center",
    minHeight: "60vh",
  },
  emptyEmoji: {
    fontSize: "80px",
    marginBottom: space[5],
    lineHeight: 1,
  },
  emptyHeading: {
    ...font["2xl"],
    fontWeight: 700,
    color: colors.fg,
    marginBottom: space[2],
  },
  emptySubtitle: {
    ...font.md,
    color: colors.muted,
    marginBottom: space[8],
  },
  errorContainer: {
    background: colors.dangerMuted,
    border: `1px solid ${colors.dangerBorder}`,
    borderRadius: "10px",
    padding: `${space[5]} ${space[6]}`,
    ...font.md,
    color: colors.danger,
  },
  skeletonCard: {
    background: colors.surface,
    border: `1px solid ${colors.border}`,
    borderRadius: radius.md,
    height: "180px",
  },
};

const pulseKeyframes = `
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }
`;

function getProgressPercent(current: number, target: number): number {
  if (target === 0) return 0;
  return Math.round((current / target) * 100);
}

function getGenreColor(genre: string): string {
  const key = genre.toLowerCase();
  return genreColors[key as keyof typeof genreColors] || genreColors["其他"];
}

interface CardProps {
  story: StoryListItem;
  onDelete: (id: string) => void;
}

function StoryCard({ story, onDelete }: CardProps) {
  const [hovered, setHovered] = useState(false);
  const [deleteHover, setDeleteHover] = useState(false);
  const progress = getProgressPercent(story.current_chapter, story.target_chapters);
  const genreColor = getGenreColor(story.genre);

  const cardStyle: CSSProperties = {
    ...styles.card,
    ...(hovered ? styles.cardHover : {}),
  };

  const deleteStyle: CSSProperties = {
    ...styles.deleteBtn,
    ...(deleteHover ? styles.deleteBtnHover : {}),
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (window.confirm(`确定要删除《${story.title}》吗？此操作不可恢复。`)) {
      onDelete(story.id);
    }
  };

  return (
    <Link
      to={`/story/${story.id}`}
      style={cardStyle}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {/* Genre color strip */}
      <div style={{
        ...styles.genreStrip,
        background: genreColor,
      }} />

      {/* Card body */}
      <div style={styles.cardBody}>
        <div style={styles.cardTitle}>{story.title}</div>
        <div style={styles.cardMeta}>
          <span style={styles.cardBadge}>{story.genre}</span>
          <span style={styles.cardBadge}>{story.style}</span>
          <span style={styles.cardStat}>{story.current_chapter}/{story.target_chapters} 章</span>
        </div>
        <div style={styles.cardProgress}>
          <div style={{
            ...styles.cardProgressBar,
            width: `${progress}%`,
            background: genreColor,
          }} />
        </div>
      </div>

      {/* Card footer */}
      <div style={styles.cardFooter}>
        <span>{story.status === "writing" ? "创作中" : story.status === "completed" ? "已完成" : "草稿"}</span>
        <button
          style={deleteStyle}
          onClick={handleDelete}
          onMouseEnter={() => setDeleteHover(true)}
          onMouseLeave={() => setDeleteHover(false)}
          title="删除故事"
        >
          删除
        </button>
      </div>
    </Link>
  );
}

function SkeletonCard() {
  return (
    <div style={styles.skeletonCard}>
      <style>{pulseKeyframes}</style>
      <div style={{
        height: "24px",
        width: "60%",
        background: colors.borderLight,
        borderRadius: "4px",
        animation: "pulse 1.5s infinite",
        marginBottom: space[3],
      }} />
      <div style={{
        display: "flex",
        gap: space[2],
        marginBottom: space[4],
      }}>
        <div style={{ height: "20px", width: "60px", background: colors.borderLight, borderRadius: "4px", animation: "pulse 1.5s infinite 0.1s" }} />
        <div style={{ height: "20px", width: "60px", background: colors.borderLight, borderRadius: "4px", animation: "pulse 1.5s infinite 0.2s" }} />
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ height: "6px", width: "100%", background: colors.borderLight, borderRadius: "3px", animation: "pulse 1.5s infinite 0.3s", marginBottom: space[2] }} />
        <div style={{ height: "6px", width: "40%", background: colors.borderLight, borderRadius: "3px", animation: "pulse 1.5s infinite 0.4s" }} />
      </div>
    </div>
  );
}

export default function StoryList() {
  const { data: stories, loading, error, refetch } = useApi<StoryListItem[]>((signal) => api.listStories({ signal }), []);

  const totalChapters = stories?.reduce((sum, s) => sum + s.current_chapter, 0) || 0;

  const handleDelete = async (id: string) => {
    try {
      await api.deleteStory(id);
      refetch();
    } catch (e) {
      alert("删除失败，请重试");
    }
  };

  if (loading) {
    return (
      <div>
        <div style={styles.pageHeader}>
          <div style={styles.headerLeft}>
            <h1 style={styles.pageTitle}>小说集</h1>
            <p style={styles.pageSubtitle}>加载中...</p>
          </div>
        </div>
        <div id="story-grid" style={styles.grid}>
          {[1, 2, 3, 4].map((i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
        <div style={{ ...layout.centered, marginTop: space[6] }}>
          <LoadingSpinner /> 加载中...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <div style={styles.pageHeader}>
          <div style={styles.headerLeft}>
            <h1 style={styles.pageTitle}>小说集</h1>
          </div>
        </div>
        <div style={styles.errorContainer}>
          加载失败：{error}
        </div>
      </div>
    );
  }

  if (!stories || stories.length === 0) {
    return (
      <div style={styles.emptyContainer}>
        <div style={styles.emptyEmoji}>📖</div>
        <h2 style={styles.emptyHeading}>还没有故事</h2>
        <p style={styles.emptySubtitle}>创建你的第一部AI小说，开启创作之旅</p>
        <Link to="/create" style={btn.primary}>
          ✨ 开始创作
        </Link>
      </div>
    );
  }

  return (
    <div>
      <div style={styles.pageHeader}>
        <div style={styles.headerLeft}>
          <h1 style={styles.pageTitle}>小说集</h1>
          <p style={styles.pageSubtitle}>
            已创作 {stories.length} 部作品 · 共 {totalChapters} 章
          </p>
        </div>
        <Link to="/create" style={styles.createBtn}>
          开始创作
        </Link>
      </div>
      <div id="story-grid" style={styles.grid}>
        {stories.map((story) => (
          <StoryCard key={story.id} story={story} onDelete={handleDelete} />
        ))}
      </div>
      <style>{`
        ${bp.md} {
          #story-grid { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </div>
  );
}