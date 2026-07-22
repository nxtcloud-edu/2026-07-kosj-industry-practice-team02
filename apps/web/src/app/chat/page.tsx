/* eslint-disable @next/next/no-html-link-for-pages */

import { ChatExperience } from "./chat-experience";

export default function ChatPage() {
  return (
    <>
      <a className="skip-link" href="#main-content">본문 바로가기</a>
      <header className="site-header">
        <div className="page-shell">
          <a className="service-name" href="/">세종 민원 AI 길잡이</a>
          <p className="header-boundary">local/private MVP</p>
        </div>
      </header>
      <main id="main-content" tabIndex={-1} className="chat-page-main">
        <div className="page-shell">
          <ChatExperience />
        </div>
      </main>
    </>
  );
}
