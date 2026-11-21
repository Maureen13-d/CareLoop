import { SearchX } from "lucide-react";
import { ButtonLink, EmptyState, Page } from "@/components/ui";

export default function NotFound() {
  return (
    <Page narrow>
      <EmptyState
        icon={<SearchX aria-hidden="true" />}
        title="That page or record does not exist"
        action={<ButtonLink href="/">Back to Today</ButtonLink>}
        className="mt-10"
      >
        It may have been closed, or the link may be wrong. Records here are synthetic.
      </EmptyState>
    </Page>
  );
}
