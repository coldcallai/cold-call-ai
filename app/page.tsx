import { landingPageHtml } from "./landing-page-html";

export default function Home() {
  return <main dangerouslySetInnerHTML={{ __html: landingPageHtml }} />;
}
