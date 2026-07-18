const supportedServices = [
  "전입·주민등록",
  "증명서 발급",
  "대형폐기물",
  "지방세 일반 안내",
] as const;

export default function Home() {
  return (
    <>
      <a className="skip-link" href="#main-content">
        본문 바로가기
      </a>

      <header className="site-header">
        <div className="page-shell">
          <span className="service-name">세종 민원 AI 길잡이</span>
        </div>
      </header>

      <main id="main-content" tabIndex={-1}>
        <section className="hero" aria-labelledby="page-title">
          <div className="page-shell hero-content">
            <p className="eyebrow">세종 시민을 위한 민원 안내 서비스</p>
            <h1 id="page-title">
              모르면 지어내지 않고,{" "}
              <br />
              알면 끝까지 안내합니다.
            </h1>
            <p className="hero-summary">
              시민의 일상어를 행정 안내와 연결하는 서비스를 준비하고 있습니다.
              근거가 확인되지 않으면 추정해서 답하지 않습니다.
            </p>
            <a className="primary-link" href="/chat">
              민원 안내 시작하기
            </a>
            <a className="text-link" href="#supported-services">
              지원 분야 확인하기
            </a>

            <aside className="development-notice" aria-labelledby="development-title">
              <p className="notice-label" id="development-title">
                개발 상태
              </p>
              <p>현재는 서비스 소개 화면을 준비한 개발 단계입니다.</p>
              <p>
                채팅 답변, 민원 신청, 개인 조회와 공식 KB 데이터는 아직 제공하지
                않습니다.
              </p>
            </aside>
          </div>
        </section>

        <section
          className="supported-services"
          id="supported-services"
          aria-labelledby="supported-services-title"
        >
          <div className="page-shell">
            <p className="section-kicker">먼저 준비하는 범위</p>
            <h2 id="supported-services-title">지원 분야</h2>
            <p className="section-summary">
              아래 네 분야부터 승인된 근거를 확인해 안내하는 것을 목표로 합니다.
              실제 신청이나 개인별 조회를 대신하지 않습니다.
            </p>
            <ul className="service-grid">
              {supportedServices.map((service) => (
                <li key={service}>{service}</li>
              ))}
            </ul>
          </div>
        </section>
      </main>

      <footer className="site-footer">
        <div className="page-shell">
          <p>세종 민원 AI 길잡이 · 로컬 개발용 소개 화면</p>
        </div>
      </footer>
    </>
  );
}
