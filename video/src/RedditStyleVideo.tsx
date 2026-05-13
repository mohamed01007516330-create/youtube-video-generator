import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { ThreadsScrollProps } from "./types";

const INTRO_SECONDS = 3;
const OUTRO_SECONDS = 4;

/* ─── Reddit-style post card ─── */
const RedditPostCard: React.FC<{
  post: ThreadsScrollProps["posts"][number];
  index: number;
}> = ({ post, index }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const slideIn = spring({ frame, fps, config: { damping: 14, stiffness: 80 } });
  const contentReveal = spring({
    frame,
    fps,
    config: { damping: 15, stiffness: 60 },
    delay: 10,
  });
  const statsReveal = spring({
    frame,
    fps,
    config: { damping: 15, stiffness: 60 },
    delay: 20,
  });

  const textGlow = interpolate(frame % 90, [0, 45, 90], [0.3, 0.6, 0.3]);

  return (
    <AbsoluteFill
      style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        padding: "60px 100px",
      }}
    >
      {/* Dark gradient background */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse at 30% 20%, #1a1a3e 0%, #0d0d1a 50%, #000000 100%)",
        }}
      />

      {/* Subtle animated grid */}
      <AbsoluteFill style={{ opacity: 0.04 }}>
        <div
          style={{
            width: "100%",
            height: "100%",
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)",
            backgroundSize: "60px 60px",
            transform: `translateY(${-frame * 0.3}px)`,
          }}
        />
      </AbsoluteFill>

      {/* Post number indicator */}
      <div
        style={{
          position: "absolute",
          top: 50,
          left: 70,
          display: "flex",
          alignItems: "center",
          gap: 14,
          opacity: slideIn,
          transform: `translateX(${interpolate(slideIn, [0, 1], [-60, 0])}px)`,
        }}
      >
        <div
          style={{
            background: "linear-gradient(135deg, #ff4500, #ff6b35)",
            borderRadius: 12,
            padding: "8px 20px",
            fontSize: 18,
            fontWeight: 800,
            color: "#fff",
            fontFamily: "Inter, system-ui, sans-serif",
            letterSpacing: 1,
          }}
        >
          #{index + 1}
        </div>
        <span
          style={{
            color: "rgba(255,255,255,0.5)",
            fontSize: 16,
            fontFamily: "Inter, system-ui, sans-serif",
          }}
        >
          {post.timeAgo}
        </span>
      </div>

      {/* Main card */}
      <div
        style={{
          background: "rgba(26, 26, 46, 0.85)",
          backdropFilter: "blur(20px)",
          borderRadius: 24,
          padding: "50px 60px",
          maxWidth: 1400,
          width: "100%",
          border: "1px solid rgba(255, 69, 0, 0.15)",
          boxShadow: `0 0 ${40 + textGlow * 20}px rgba(255, 69, 0, ${0.05 + textGlow * 0.05}),
                      0 20px 60px rgba(0, 0, 0, 0.5)`,
          opacity: slideIn,
          transform: `translateY(${interpolate(slideIn, [0, 1], [60, 0])}px)`,
        }}
      >
        {/* User info row */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 16,
            marginBottom: 30,
          }}
        >
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: "50%",
              background: `linear-gradient(135deg, ${post.avatarColor || "#ff4500"}, ${post.avatarColor || "#ff4500"}88)`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 28,
              boxShadow: `0 0 20px ${post.avatarColor || "#ff4500"}40`,
            }}
          >
            {post.avatarEmoji || "👤"}
          </div>
          <div>
            <div
              style={{
                color: "#ff6b35",
                fontSize: 22,
                fontWeight: 700,
                fontFamily: "Inter, system-ui, sans-serif",
              }}
            >
              @{post.username}
            </div>
            <div
              style={{
                color: "rgba(255,255,255,0.4)",
                fontSize: 14,
                fontFamily: "Inter, system-ui, sans-serif",
                marginTop: 2,
              }}
            >
              Threads
            </div>
          </div>
        </div>

        {/* Post content with typewriter-like reveal */}
        <div
          style={{
            color: "#f0f0f0",
            fontSize: 36,
            fontFamily: "Inter, system-ui, sans-serif",
            fontWeight: 500,
            lineHeight: 1.6,
            whiteSpace: "pre-wrap",
            opacity: contentReveal,
            transform: `translateY(${interpolate(contentReveal, [0, 1], [20, 0])}px)`,
            borderLeft: "3px solid #ff4500",
            paddingLeft: 24,
          }}
        >
          {post.content}
        </div>

        {/* Meme image (from Pinterest) */}
        {post.memeImage && (
          <div
            style={{
              marginTop: 20,
              display: "flex",
              justifyContent: "center",
              opacity: contentReveal,
              transform: `scale(${interpolate(contentReveal, [0, 1], [0.9, 1])})`,
            }}
          >
            <Img
              src={staticFile(post.memeImage)}
              style={{
                maxWidth: 400,
                maxHeight: 300,
                borderRadius: 16,
                border: "2px solid rgba(255, 69, 0, 0.2)",
                objectFit: "contain",
              }}
            />
          </div>
        )}

        {/* Engagement stats */}
        <div
          style={{
            display: "flex",
            gap: 40,
            marginTop: 35,
            paddingTop: 25,
            borderTop: "1px solid rgba(255,255,255,0.08)",
            opacity: statsReveal,
            transform: `translateY(${interpolate(statsReveal, [0, 1], [15, 0])}px)`,
          }}
        >
          {[
            { icon: "❤️", value: post.likes || 0, label: "likes" },
            { icon: "💬", value: post.comments || 0, label: "comments" },
            { icon: "🔄", value: post.reposts || 0, label: "reposts" },
          ].map((stat) => (
            <div
              key={stat.label}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
              }}
            >
              <span style={{ fontSize: 22 }}>{stat.icon}</span>
              <span
                style={{
                  color: "rgba(255,255,255,0.7)",
                  fontSize: 20,
                  fontFamily: "Inter, system-ui, sans-serif",
                  fontWeight: 600,
                }}
              >
                {stat.value >= 1000
                  ? `${(stat.value / 1000).toFixed(1)}K`
                  : stat.value}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom narration indicator */}
      <div
        style={{
          position: "absolute",
          bottom: 50,
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          opacity: statsReveal * 0.6,
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            color: "rgba(255,255,255,0.4)",
            fontSize: 16,
            fontFamily: "Inter, system-ui, sans-serif",
          }}
        >
          <span>🔊</span>
          <span>Đang nghe...</span>
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* ─── Intro card ─── */
const IntroCard: React.FC<{ postCount: number }> = ({ postCount }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const appear = spring({ frame, fps, config: { damping: 12, stiffness: 80 } });
  const pulse = interpolate(frame % 60, [0, 30, 60], [1, 1.02, 1]);

  return (
    <AbsoluteFill
      style={{
        background:
          "radial-gradient(ellipse at 50% 40%, #1a1a3e, #0a0a14)",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <div
        style={{
          textAlign: "center",
          opacity: appear,
          transform: `scale(${appear * pulse})`,
        }}
      >
        <div style={{ fontSize: 60, marginBottom: 20 }}>🧵</div>
        <div
          style={{
            fontSize: 52,
            fontWeight: 800,
            color: "#fff",
            fontFamily: "Inter, system-ui, sans-serif",
            marginBottom: 16,
          }}
        >
          Threads Hot Today
        </div>
        <div
          style={{
            fontSize: 26,
            color: "rgba(255,255,255,0.5)",
            fontFamily: "Inter, system-ui, sans-serif",
          }}
        >
          Top {postCount} bài đăng viral
        </div>
        <div
          style={{
            width: 80,
            height: 4,
            background: "linear-gradient(90deg, #ff4500, #ff6b35)",
            borderRadius: 2,
            margin: "24px auto 0",
          }}
        />
      </div>
    </AbsoluteFill>
  );
};

/* ─── Outro card ─── */
const OutroCardReddit: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const appear = spring({ frame, fps, config: { damping: 12 } });

  return (
    <AbsoluteFill
      style={{
        background:
          "radial-gradient(ellipse at 50% 40%, #1a1a3e, #0a0a14)",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <div style={{ textAlign: "center", opacity: appear }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>🔔</div>
        <div
          style={{
            fontSize: 44,
            fontWeight: 800,
            color: "#fff",
            fontFamily: "Inter, system-ui, sans-serif",
            marginBottom: 12,
          }}
        >
          Follow & Subscribe
        </div>
        <div
          style={{
            fontSize: 22,
            color: "rgba(255,255,255,0.5)",
            fontFamily: "Inter, system-ui, sans-serif",
          }}
        >
          Like & Share nha!
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* ─── Main composition ─── */
export const RedditStyleVideo: React.FC<ThreadsScrollProps> = ({
  posts,
  fps,
  backgroundMusic,
  backgroundMusicVolume,
}) => {
  const effectiveFps = fps || 30;
  const bgMusicVol = backgroundMusicVolume ?? 0.12;
  const introDuration = INTRO_SECONDS * effectiveFps;
  const outroDuration = OUTRO_SECONDS * effectiveFps;

  let currentFrame = introDuration;

  return (
    <AbsoluteFill>
      {/* Background music */}
      {backgroundMusic && (
        <Audio src={staticFile(backgroundMusic)} volume={bgMusicVol} loop />
      )}

      {/* Intro */}
      <Sequence from={0} durationInFrames={introDuration}>
        <IntroCard postCount={posts.length} />
      </Sequence>

      {/* Posts */}
      {posts.map((post, index) => {
        const postDuration = Math.round(post.durationInSeconds * effectiveFps);
        const from = currentFrame;
        currentFrame += postDuration;

        return (
          <Sequence key={index} from={from} durationInFrames={postDuration}>
            <RedditPostCard post={post} index={index} />
            {post.audioFile && (
              <Audio src={staticFile(post.audioFile)} volume={0.9} />
            )}
          </Sequence>
        );
      })}

      {/* Outro */}
      <Sequence from={currentFrame} durationInFrames={outroDuration}>
        <OutroCardReddit />
      </Sequence>
    </AbsoluteFill>
  );
};
