import { Link } from "react-router-dom"

/* ─── Feature icons (inline SVG) ──────────────────────────────── */
function IconCompress() {
  return (
    <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M8 3H5a2 2 0 0 0-2 2v3" />
      <path d="M21 8V5a2 2 0 0 0-2-2h-3" />
      <path d="M3 16v3a2 2 0 0 0 2 2h3" />
      <path d="M16 21h3a2 2 0 0 0 2-2v-3" />
      <path d="M12 8v8" />
      <path d="M8 12h8" />
    </svg>
  )
}
function IconLock() {
  return (
    <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
    </svg>
  )
}
function IconChart() {
  return (
    <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="20" x2="18" y2="10" />
      <line x1="12" y1="20" x2="12" y2="4" />
      <line x1="6" y1="20" x2="6" y2="14" />
    </svg>
  )
}
function IconImage() {
  return (
    <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <circle cx="8.5" cy="8.5" r="1.5" />
      <polyline points="21 15 16 10 5 21" />
    </svg>
  )
}
function IconAudio() {
  return (
    <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 18V5l12-2v13" />
      <circle cx="6" cy="18" r="3" />
      <circle cx="18" cy="16" r="3" />
    </svg>
  )
}
function IconVideo() {
  return (
    <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="23 7 16 12 23 17 23 7" />
      <rect x="1" y="5" width="15" height="14" rx="2" />
    </svg>
  )
}

/* ─── Media card ──────────────────────────────────────────────── */
interface MediaCardProps {
  to: string
  icon: React.ReactNode
  title: string
  description: string
  tags: string[]
  accentColor: string
}

function MediaCard({ to, icon, title, description, tags, accentColor }: MediaCardProps) {
  return (
    <Link
      to={to}
      style={{ textDecoration: "none" }}
    >
      <div
        style={{
          background: "var(--color-surface)",
          border: "1px solid var(--color-border)",
          borderRadius: "var(--radius-lg)",
          padding: "1.75rem",
          cursor: "pointer",
          transition: "all 200ms cubic-bezier(0.4,0,0.2,1)",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          gap: "1rem",
          position: "relative",
          overflow: "hidden",
        }}
        onMouseEnter={(e) => {
          const el = e.currentTarget
          el.style.borderColor = accentColor
          el.style.transform = "translateY(-3px)"
          el.style.boxShadow = `0 8px 32px rgba(0,0,0,0.35), 0 0 0 1px ${accentColor}33`
        }}
        onMouseLeave={(e) => {
          const el = e.currentTarget
          el.style.borderColor = "var(--color-border)"
          el.style.transform = "translateY(0)"
          el.style.boxShadow = "none"
        }}
      >
        {/* Gradient accent top-left */}
        <div style={{
          position: "absolute", top: 0, left: 0, right: 0, height: "3px",
          background: `linear-gradient(90deg, ${accentColor}, transparent)`,
          borderRadius: "var(--radius-lg) var(--radius-lg) 0 0",
        }} />

        {/* Icon */}
        <div style={{
          width: "3rem", height: "3rem",
          background: `${accentColor}1a`,
          border: `1px solid ${accentColor}33`,
          borderRadius: "0.75rem",
          display: "flex", alignItems: "center", justifyContent: "center",
          color: accentColor,
          flexShrink: 0,
        }}>
          {icon}
        </div>

        <div style={{ flex: 1 }}>
          <h3 style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: "0.5rem", color: "var(--color-text)" }}>{title}</h3>
          <p style={{ color: "var(--color-muted)", fontSize: "0.9375rem", lineHeight: 1.6, margin: 0 }}>{description}</p>
        </div>

        {/* Tags */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.375rem" }}>
          {tags.map((tag) => (
            <span key={tag} style={{
              fontSize: "0.75rem", fontWeight: 600, padding: "0.2rem 0.6rem",
              borderRadius: "999px", color: "var(--color-muted-2)",
              background: "var(--color-surface-2)", border: "1px solid var(--color-border)",
            }}>
              {tag}
            </span>
          ))}
        </div>

        {/* Arrow */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.375rem", color: accentColor, fontSize: "0.875rem", fontWeight: 600 }}>
          <span>Get started</span>
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
            <path d="M5 12h14M12 5l7 7-7 7" />
          </svg>
        </div>
      </div>
    </Link>
  )
}

/* ─── Feature row ─────────────────────────────────────────────── */
function FeatureItem({ icon, title, desc }: { icon: React.ReactNode; title: string; desc: string }) {
  return (
    <div style={{ display: "flex", gap: "1rem", alignItems: "flex-start" }}>
      <div style={{
        width: "2.25rem", height: "2.25rem",
        background: "rgba(34,197,94,0.12)", border: "1px solid rgba(34,197,94,0.2)",
        borderRadius: "0.625rem", display: "flex", alignItems: "center", justifyContent: "center",
        color: "var(--color-primary)", flexShrink: 0,
      }}>{icon}</div>
      <div>
        <p style={{ fontWeight: 600, color: "var(--color-text)", margin: "0 0 0.25rem", fontSize: "0.9375rem" }}>{title}</p>
        <p style={{ color: "var(--color-muted)", margin: 0, fontSize: "0.875rem", lineHeight: 1.6 }}>{desc}</p>
      </div>
    </div>
  )
}

/* ─── HomePage ─────────────────────────────────────────────────── */
export function HomePage() {
  return (
    <div>
      {/* ── Hero ────────────────────────────────────────────────── */}
      <section style={{
        padding: "5rem 1.5rem 4rem",
        textAlign: "center",
        position: "relative",
        overflow: "hidden",
      }}>
        {/* Radial glow background */}
        <div style={{
          position: "absolute", top: "-10rem", left: "50%", transform: "translateX(-50%)",
          width: "60rem", height: "40rem",
          background: "radial-gradient(ellipse at center, rgba(34,197,94,0.08) 0%, transparent 70%)",
          pointerEvents: "none",
        }} />

        <div className="container-lg" style={{ position: "relative" }}>
          {/* Pill badge */}
          <div className="animate-fade-up" style={{ marginBottom: "1.5rem" }}>
            <span className="feature-pill">
              <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" /></svg>
              Media Compression + Steganography
            </span>
          </div>

          {/* Headline */}
          <h1 className="animate-fade-up animate-delay-1" style={{ fontSize: "clamp(2.5rem,6vw,4rem)", fontWeight: 800, marginBottom: "1.25rem" }}>
            Compress, Hide, and{" "}
            <span className="gradient-text">Protect Your Media</span>
          </h1>

          {/* Subtitle */}
          <p className="animate-fade-up animate-delay-2" style={{
            fontSize: "1.125rem", color: "var(--color-muted)", maxWidth: "38rem",
            margin: "0 auto 2.5rem", lineHeight: 1.7,
          }}>
            Professional-grade media compression with built-in steganography — hide encrypted messages inside images, audio, and video files. Measure quality with PSNR, SSIM & compression metrics.
          </p>

          {/* CTA row */}
          <div className="animate-fade-up animate-delay-3" style={{ display: "flex", gap: "0.75rem", justifyContent: "center", flexWrap: "wrap" }}>
            <Link to="/image" className="btn btn-primary" style={{ fontSize: "1rem", padding: "0.75rem 2rem" }}>
              Start Compressing
            </Link>
            <Link to="/jobs" className="btn btn-ghost" style={{ fontSize: "1rem", padding: "0.75rem 2rem" }}>
              View Job History
            </Link>
          </div>

          {/* Stats */}
          <div style={{
            display: "flex", gap: "2.5rem", justifyContent: "center", flexWrap: "wrap",
            marginTop: "3.5rem", paddingTop: "3rem", borderTop: "1px solid var(--color-border)",
          }}>
            {[
              { label: "Algorithms", value: "4+" },
              { label: "Media Types", value: "3" },
              { label: "Quality Metrics", value: "PSNR/SSIM" },
              { label: "Encryption", value: "AES-256" },
            ].map((stat) => (
              <div key={stat.label} style={{ textAlign: "center" }}>
                <div style={{ fontSize: "1.75rem", fontWeight: 800, color: "var(--color-primary)", letterSpacing: "-0.03em" }}>{stat.value}</div>
                <div style={{ fontSize: "0.8125rem", color: "var(--color-muted)", fontWeight: 500, marginTop: "0.25rem" }}>{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Media Cards ──────────────────────────────────────────── */}
      <section style={{ padding: "2rem 1.5rem 4rem" }}>
        <div className="container-lg">
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(280px,1fr))", gap: "1.25rem" }}>
            <MediaCard
              to="/image"
              icon={<IconImage />}
              title="Image"
              description="Compress PNG/JPEG with RLE or Huffman, embed hidden messages with LSB steganography, decrypt and compare with PSNR/SSIM metrics."
              tags={["RLE", "Huffman", "LSB Stego", "PSNR/SSIM"]}
              accentColor="#22c55e"
            />
            <MediaCard
              to="/audio"
              icon={<IconAudio />}
              title="Audio"
              description="Compress WAV to MP3, hide encrypted messages in PCM audio samples via LSB steganography, with full roundtrip verification."
              tags={["WAV→MP3", "PCM LSB", "AES Encrypt"]}
              accentColor="#38bdf8"
            />
            <MediaCard
              to="/video"
              icon={<IconVideo />}
              title="Video"
              description="H.264 MP4 compression with configurable CRF quality, I-frame-based steganography for embedding and extracting hidden messages."
              tags={["H.264", "CRF Control", "I-Frame Stego"]}
              accentColor="#a78bfa"
            />
          </div>
        </div>
      </section>

      {/* ── Features ─────────────────────────────────────────────── */}
      <section style={{ padding: "2rem 1.5rem 5rem" }}>
        <div className="container-lg">
          <div style={{
            display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(280px,1fr))",
            gap: "2rem",
            background: "var(--color-surface)", border: "1px solid var(--color-border)",
            borderRadius: "var(--radius-lg)", padding: "2.5rem",
          }}>
            <div>
              <h2 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "1.5rem" }}>
                Why mycompress?
              </h2>
              <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
                <FeatureItem icon={<IconCompress />} title="Multi-algorithm Compression" desc="RLE, Huffman, and FFmpeg-based codecs for lossy/lossless trade-offs." />
                <FeatureItem icon={<IconLock />} title="Built-in AES-256 Encryption" desc="Optionally encrypt your hidden payload before embedding — password-protected steganography." />
                <FeatureItem icon={<IconChart />} title="Quality Metrics" desc="PSNR, SSIM, MSE, and compression ratio computed for every job automatically." />
              </div>
            </div>

            <div style={{
              background: "var(--color-bg)",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius)",
              padding: "1.5rem",
              fontFamily: "ui-monospace, monospace",
              fontSize: "0.8125rem",
              lineHeight: 1.8,
              color: "var(--color-muted)",
              display: "flex",
              flexDirection: "column",
              justifyContent: "center",
            }}>
              <p style={{ color: "#4ade80", margin: "0 0 0.5rem" }}># Typical workflow</p>
              <p style={{ margin: "0.25rem 0" }}><span style={{ color: "#38bdf8" }}>POST</span> /api/v1/image/embed</p>
              <p style={{ margin: "0.25rem 0 0.75rem" }}>  file=photo.png msg="secret"</p>
              <p style={{ margin: "0.25rem 0" }}><span style={{ color: "#4ade80" }}>→ 200 OK</span> job_id: a1b2c3...</p>
              <p style={{ margin: "0.25rem 0" }}><span style={{ color: "#38bdf8" }}>GET</span>  /api/v1/jobs/a1b2c3</p>
              <p style={{ margin: "0.25rem 0 0.75rem" }}><span style={{ color: "#4ade80" }}>→ done</span> psnr=48.2 ssim=0.99</p>
              <p style={{ margin: "0.25rem 0" }}><span style={{ color: "#38bdf8" }}>POST</span> /api/v1/image/extract</p>
              <p style={{ margin: "0.25rem 0" }}><span style={{ color: "#4ade80" }}>→ "secret"</span></p>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}