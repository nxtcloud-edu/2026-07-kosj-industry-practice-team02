/* eslint-disable @next/next/no-html-link-for-pages */

import { notFound } from "next/navigation";

import { AdminExperience } from "./admin-experience";

export const dynamic = "force-dynamic";

export default function AdminPage() {
  if (process.env.ADMIN_UI_ENABLED !== "true") {
    notFound();
  }
  const transportMode = process.env.ADMIN_UI_MODE === "actual" ? "actual" : "fixture";

  return (
    <>
      <a className="skip-link" href="#admin-main">본문 바로가기</a>
      <header className="site-header">
        <div className="page-shell">
          <a className="service-name" href="/">세종 민원 AI 길잡이</a>
          <p className="header-boundary">local/private 관리자 시연</p>
        </div>
      </header>
      <main id="admin-main" tabIndex={-1}>
        <AdminExperience transportMode={transportMode} />
      </main>
    </>
  );
}
