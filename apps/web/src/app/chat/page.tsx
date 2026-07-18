/* eslint-disable @next/next/no-html-link-for-pages */

const supportedServices = [
  "전입·주민등록",
  "증명서 발급",
  "대형폐기물",
  "지방세 일반 안내",
] as const;

export default function ChatPreparationPage() {
  return (
    <>
      <a className="skip-link" href="#main-content">
        본문 바로가기
      </a>

      <header className="site-header">
        <div className="page-shell">
          <a className="service-name" href="/">
            세종 민원 AI 길잡이
          </a>
        </div>
      </header>

      <main id="main-content" tabIndex={-1}>
        <section className="chat-shell" aria-labelledby="chat-page-title">
          <div className="page-shell chat-shell-content">
            <p className="eyebrow">안전한 안내를 위한 준비 단계</p>
            <h1 id="chat-page-title">민원 안내 채팅을 준비하고 있습니다.</h1>
            <p className="chat-summary">
              승인된 공식 근거를 확인한 뒤, 알 수 있는 내용만 끝까지 안내하겠습니다.
            </p>

            <aside className="development-notice" aria-labelledby="chat-limit-title">
              <p className="notice-label" id="chat-limit-title">
                현재 제공하지 않는 기능
              </p>
              <p>
                채팅 답변, 민원 신청, 개인별 조회와 공식 KB 데이터는 아직 제공하지 않습니다.
              </p>
            </aside>

            <section className="chat-scope" aria-labelledby="chat-scope-title">
              <p className="section-kicker">준비 중인 범위</p>
              <h2 id="chat-scope-title">준비 중인 지원 분야</h2>
              <ul className="chat-info-grid">
                {supportedServices.map((service) => (
                  <li key={service}>{service}</li>
                ))}
              </ul>
            </section>

            <a className="secondary-link" href="/">
              소개 화면으로 돌아가기
            </a>
          </div>
        </section>
      </main>
    </>
  );
}
